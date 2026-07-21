import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from structlog.testing import capture_logs

from finlib.async_fetch import (
    BinanceDataRow,
    _convert_binance_data_to_DataFrame,
    _fetch_binance_one_symbol_with_retry,
    _fetch_binance_raw_data,
    _validated_fetch_binance_one_symbol,
    binance_interval,
    fetch_binance,
)
from finlib.config import get_settings

_EX_DT = datetime(2026,7,1,0,0,0)
_EX_DEC = Decimal(103.5)
_EX_INT = 1214
_EX_STR = "0"

_EX_ROW = [_EX_DT, _EX_DEC, _EX_DEC, _EX_DEC, _EX_DEC, _EX_DEC, 
           _EX_DT, _EX_DEC, _EX_INT, _EX_DEC, _EX_DEC, _EX_STR]

_EX_ROW_BROW = BinanceDataRow.from_list(_EX_ROW)

async def test_stream_binance_data_interval() -> None:
    with pytest.raises(ValueError):
        _ = await fetch_binance(["BTCUSDT"], "13m", _EX_DT) # type: ignore # this is a test

async def test_stream_binance_data_symbol_type() -> None:
    with pytest.raises(TypeError):
        _ = await fetch_binance("BTCUSDT", "1m", _EX_DT) # type: ignore # this is a test

async def test_fetch_binance_data_happy_path() -> None:
    with patch('finlib.async_fetch._fetch_binance_one_symbol', 
                          new_callable=AsyncMock) as mock:
        mock.return_value = [_EX_ROW]
        result = await _fetch_binance_raw_data(['SYM'], "1m", 1)
    assert result["SYM"] is not None
    assert len(result["SYM"])==1
    assert result['SYM'][0].open_time == _EX_DT

async def test_fetch_binance_data_malformed_data() -> None:
    with patch('finlib.async_fetch._fetch_binance_one_symbol', 
                          new_callable=AsyncMock) as mock:
        mock.return_value = [_EX_ROW, _EX_ROW[1:]]
        result = await _fetch_binance_raw_data(['SYM'], "1m", 2)
    assert result["SYM"] is not None
    assert len(result["SYM"])==1
    assert result['SYM'][0].open_time == _EX_DT

async def test_fetch_binance_data_client_response_error() -> None:
    with patch('finlib.async_fetch._fetch_binance_one_symbol', 
                          new_callable=AsyncMock) as mock:
        mock.side_effect = aiohttp.client_exceptions.ClientResponseError("x", "y") # type: ignore # this is a test
        result = await _fetch_binance_raw_data(['SYM'], "1m",1)
    assert result["SYM"] is None

async def test_fetch_binance_semaphore() -> None:
    settings = get_settings()
    max_concurrent = settings.binance.max_number_concurrent_calls
    active_count = 0
    peak_active = 0
    lock = asyncio.Lock()

    async def slow_fetch(session: aiohttp.ClientSession,
                         symbol: str, 
                         interval: binance_interval, 
                         limit: int) -> list[BinanceDataRow]:
        nonlocal active_count, peak_active
        async with lock:
            active_count+=1
            peak_active = max(peak_active, active_count)
        await asyncio.sleep(0.02)
        async with lock:
            active_count-=1
        return [_EX_ROW_BROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol', 
                          new_callable=AsyncMock) as mock:
        mock.side_effect = slow_fetch
        ten_symbols = [f"SYM{n}" for n in range(10)]
        _ = await _fetch_binance_raw_data(ten_symbols, "1m", 1)
    assert peak_active==max_concurrent

        
async def test_fetch_binance_retry() -> None:
    max_retry = 3
    count = 0
    lock = asyncio.Lock()

    async def retry_fetch(session: aiohttp.ClientSession,
                          symbol: str, 
                          interval: binance_interval, 
                          limit: int) -> list[BinanceDataRow]:
        nonlocal count
        async with lock:
            count +=1
        if count<max_retry:
            raise aiohttp.ClientError
        return [_EX_ROW_BROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol', 
                          new_callable=AsyncMock) as mock:
        mock.side_effect = retry_fetch
        _ = await _fetch_binance_raw_data(["SYM"], "1m", 1)
    assert count==max_retry


def test_convert_binance_data_to_DataFrame_symbol_data_missing() -> None:
    assert (_convert_binance_data_to_DataFrame({"SYM1": [_EX_ROW_BROW], "SYM2": None}) == 
            _convert_binance_data_to_DataFrame({"SYM1": [_EX_ROW_BROW]})).all().all()


async def test_validated_fetch_binance_one_symbol_invalid_rows_count() -> None:
    semaphore = asyncio.Semaphore(1)

    async def malformed_rows(session: aiohttp.ClientSession,
                             symbol: str, 
                             interval: binance_interval, 
                             limit: int) -> list[list[Any]]:
        return [_EX_ROW, _EX_ROW[1:], _EX_ROW[1:], _EX_ROW, _EX_ROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol_with_retry', 
                          new_callable=AsyncMock) as mock:
        mock.side_effect = malformed_rows
        with capture_logs() as logs:
            _ = await _validated_fetch_binance_one_symbol(aiohttp.ClientSession(), 
                                                          "AAA", "1m", 1, semaphore)
            assert logs[0]["invalid_rows_count"]==2

async def test_validated_fetch_binance_one_symbol_invalid_rows_remaining_output() -> None:
    semaphore = asyncio.Semaphore(1)

    async def malformed_rows(session: aiohttp.ClientSession,
                             symbol: str, 
                             interval: binance_interval, 
                             limit: int) -> list[list[Any]]:
        return [_EX_ROW, _EX_ROW[1:], _EX_ROW[1:], _EX_ROW, _EX_ROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol_with_retry', 
                          new_callable=AsyncMock) as mock:
        mock.side_effect = malformed_rows
        result = await _validated_fetch_binance_one_symbol(aiohttp.ClientSession(), 
                                                          "AAA", "1m", 1, semaphore)
        assert result == 3*[_EX_ROW_BROW]

@pytest.mark.parametrize("exception", [aiohttp.ClientError, asyncio.TimeoutError])
async def test_fetch_binance_one_symbol_with_retry_timeout_retry(
    exception: type[Exception]) -> None:
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value=[_EX_ROW])

    mock_get_cm = AsyncMock()
    mock_get_cm.__aenter__.return_value = mock_response

    session = AsyncMock()
    session.get = MagicMock(side_effect=[exception, mock_get_cm])

    res = await _fetch_binance_one_symbol_with_retry(session, "SYM", "1m", 1)
    assert res == [_EX_ROW]

async def test_fetch_binance_raw_data_malformed_rows_skipped() -> None:

    def make_get_cm(url: str, params: dict[str, str | int], **kwargs: object) -> AsyncMock:
        rows = [_EX_ROW[1:], _EX_ROW[1:]] if params["symbol"] == "AAA" else [_EX_ROW, _EX_ROW]
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=rows)

        mock_get_cm = AsyncMock()
        mock_get_cm.__aenter__.return_value = mock_response
        return mock_get_cm

    session = AsyncMock()
    session.get = MagicMock(side_effect=make_get_cm)

    with patch("finlib.async_fetch.aiohttp.ClientSession") as mock:
        mock.return_value.__aenter__ = AsyncMock(return_value=session)
        res = await _fetch_binance_raw_data(["AAA", "BBB"], "1m", 2)
        assert res["AAA"] == []
        assert res["BBB"] == 2*[_EX_ROW_BROW]

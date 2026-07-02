from finlib.async_fetch import BinanceDataRow, fetch_binance, _fetch_binance_raw_data, _convert_binance_data_to_DataFrame
import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
import asyncio
from finlib.config import get_settings
from datetime import datetime
from decimal import Decimal

_EX_DT = datetime(2026,7,1,0,0,0)
_EX_DEC = Decimal(103.5)
_EX_INT = 1214
_EX_STR = "0"

_EX_ROW = [_EX_DT, _EX_DEC, _EX_DEC, _EX_DEC, _EX_DEC, _EX_DEC, _EX_DT, _EX_DEC, _EX_INT, _EX_DEC, _EX_DEC, _EX_STR]

def test_stream_binance_data_interval():
    with pytest.raises(ValueError):
        _ = fetch_binance(["BTCUSDT"], "13m", _EX_DT)

def test_stream_binance_data_symbol_type():
    with pytest.raises(TypeError):
        _ = fetch_binance("BTCUSDT", "1m", _EX_DT)

async def test_fetch_binance_data_happy_path():
    with patch('finlib.async_fetch._fetch_binance_one_symbol', new_callable=AsyncMock) as mock:
        mock.return_value = [_EX_ROW]
        result = await _fetch_binance_raw_data(['SYM'], "1m", 1)
    assert (len(result["SYM"])==1) and (result["SYM"] is not None) and (result['SYM'][0].open_time == _EX_DT)

async def test_fetch_binance_data_malformed_data():
    with patch('finlib.async_fetch._fetch_binance_one_symbol', new_callable=AsyncMock) as mock:
        mock.return_value = [_EX_ROW, _EX_ROW[1:]]
        result = await _fetch_binance_raw_data(['SYM'], "1m", 2)
    assert (len(result["SYM"])==1) and (result['SYM'][0].open_time == _EX_DT)

async def test_fetch_binance_data_client_response_error():
    with patch('finlib.async_fetch._fetch_binance_one_symbol', new_callable=AsyncMock) as mock:
        mock.side_effect = aiohttp.client_exceptions.ClientResponseError("x", "y")
        result = await _fetch_binance_raw_data(['SYM'], "1m",1)
    assert result["SYM"] is None

async def test_fetch_binance_semaphore():
    settings = get_settings()
    max_concurrent = settings.binance.max_number_concurrent_calls
    active_count = 0
    peak_active = 0
    lock = asyncio.Lock()

    async def slow_fetch(session, symbol, interval, limit):
        nonlocal active_count, peak_active
        async with lock:
            active_count+=1
            peak_active = max(peak_active, active_count)
        await asyncio.sleep(0.02)
        async with lock:
            active_count-=1
        return [_EX_ROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol', new_callable=AsyncMock) as mock:
        mock.side_effect = slow_fetch
        ten_symbols = [f"SYM{n}" for n in range(10)]
        _ = await _fetch_binance_raw_data(ten_symbols, "1m", 1)
    assert peak_active==max_concurrent

        
async def test_fetch_binance_retry():
    max_retry = 3
    count = 0
    lock = asyncio.Lock()

    async def retry_fetch(session, symbol, interval, limit):
        nonlocal count
        async with lock:
            count +=1
        if count<max_retry:
            raise aiohttp.ClientError
        else:
            return [_EX_ROW]

    with patch('finlib.async_fetch._fetch_binance_one_symbol', new_callable=AsyncMock) as mock:
        mock.side_effect = retry_fetch
        _ = await _fetch_binance_raw_data(["SYM"], "1m", 1)
    assert count==max_retry


def test_convert_binance_data_to_DataFrame_symbol_data_missing():
    brow = BinanceDataRow(**{k:v for k,v in zip(BinanceDataRow.model_fields, _EX_ROW)})
    assert (_convert_binance_data_to_DataFrame({"SYM1": [brow], "SYM2": None}) == _convert_binance_data_to_DataFrame({"SYM1": [brow]})).all().all()
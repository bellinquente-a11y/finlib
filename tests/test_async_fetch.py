from finlib.async_fetch import stream_binance_data, fetch_binance_data
import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
import asyncio
from finlib.config import get_settings

def test_stream_binance_data_interval():
    with pytest.raises(ValueError):
        _ = stream_binance_data(["BTCUSDT"], "13m")

def test_stream_binance_data_symbol_type():
    with pytest.raises(TypeError):
        _ = stream_binance_data("BTCUSDT", "1m")

async def test_fetch_binance_data_happy_path():
    with patch('finlib.async_fetch.fetch_binance_one_symbol_one_row', new_callable=AsyncMock) as mock:
        mocked_output = [[1782707280000, '59969.64000000','59972.00000000','59941.03000000', '59941.03000000', '7.63798000', 
                          1782707339999, '458032.05198250', 1714, '0.66735000', '40088.75994900', '0']]
        mock.return_value = mocked_output
        result = await fetch_binance_data(['SYM'], "1m")
    assert result is not None and result['SYM'].open_time == 1782707280000

async def test_fetch_binance_data_malformed_data():
    with patch('finlib.async_fetch.fetch_binance_one_symbol_one_row', new_callable=AsyncMock) as mock:
        mocked_output = [['59969.64000000','59972.00000000','59941.03000000', '59941.03000000', '7.63798000', 
                          1782707339999, '458032.05198250', 1714, '0.66735000', '40088.75994900', '0']]
        mock.return_value = mocked_output
        result = await fetch_binance_data(['SYM'], "1m")
    assert result['SYM'] is None

async def test_fetch_binance_data_client_response_error():
    with patch('finlib.async_fetch.fetch_binance_one_symbol_one_row', new_callable=AsyncMock) as mock:
        mock.side_effect = aiohttp.client_exceptions.ClientResponseError("x", "y")
        result = await fetch_binance_data(['SYM'], "1m")
    assert result["SYM"] is None

async def test_fetch_binance_semaphore():
    settings = get_settings()
    max_concurrent = settings.binance.max_number_concurrent_calls
    active_count = 0
    peak_active = 0
    lock = asyncio.Lock()

    async def slow_fetch(session, symbol, interval):
        nonlocal active_count, peak_active
        async with lock:
            active_count+=1
            peak_active = max(peak_active, active_count)
        await asyncio.sleep(0.2)
        async with lock:
            active_count-=1
        return [[1782707280000, '59969.64000000','59972.00000000','59941.03000000', '59941.03000000', '7.63798000', 
                          1782707339999, '458032.05198250', 1714, '0.66735000', '40088.75994900', '0']]

    with patch('finlib.async_fetch.fetch_binance_one_symbol_one_row', new_callable=AsyncMock) as mock:
        mock.side_effect = slow_fetch
        ten_symbols = [f"SYM{n}" for n in range(10)]
        _ = await fetch_binance_data(ten_symbols, "1m")
    assert peak_active==max_concurrent

        
async def test_fetch_binance_retry():
    max_retry = 3
    count = 0
    lock = asyncio.Lock()

    async def retry_fetch(session, symbol, interval):
        nonlocal count
        async with lock:
            count +=1
        if count<max_retry:
            raise aiohttp.ClientError
        else:
            return [[1782707280000, '59969.64000000','59972.00000000','59941.03000000', '59941.03000000', '7.63798000', 
                          1782707339999, '458032.05198250', 1714, '0.66735000', '40088.75994900', '0']]

    with patch('finlib.async_fetch.fetch_binance_one_symbol_one_row', new_callable=AsyncMock) as mock:
        mock.side_effect = retry_fetch
        _ = await fetch_binance_data(["SYM"], "1m")
    assert count==max_retry
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from string import ascii_uppercase
from finlib.utils import timer

def fetch_price(symbol: str) -> float:
    """Function to simulate network latency"""
    if not isinstance(symbol, str):
        raise TypeError
    if not symbol.isupper():
        raise ValueError
    if symbol in ["BBB", "EEE"]:
        raise ConnectionError(f"connection error for {symbol}")
    time.sleep(0.2)
    return float(hash(symbol))

symbols = [3*ascii_uppercase[i] for i in range(10)]

results: dict[str, float] = {}
errors: dict[str, Exception] = {}

for workers in (1, 2, 5, 10, 20):
    with timer(f"{workers:>2} workers"):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(fetch_price, symbol):symbol for symbol in symbols}
        for f in as_completed(futures.keys()):
            try:
                results[futures[f]] = f.result()
            except ConnectionError as e:
                errors[futures[f]] = e
        for k, v in results.items():
            print(f"{k} {v:.3e}")
        for err in errors.values():
            print(err)

    
import time
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from string import ascii_uppercase
# from finlib.context_managers import timer
import structlog

log = structlog.get_logger()

def fetch_price(symbol: str) -> float | None:
    """Function to simulate network latency"""
    start = time.perf_counter()
    if not symbol.isupper():
        raise ValueError

    time.sleep(0.02)
    end = time.perf_counter()
    try:    
        if symbol in ["BBB", "EEE"]:
            raise ConnectionError
        else:
            price = hash(symbol) % 100 + 0.5 
            log.info("Fetched price", symbol=symbol, price=price, latency=end-start)
            return price
    except Exception as e:
        log.error("Issue with fetching", symbol=symbol, error=e)
        return None

# if __name__ == "__main__":

#     symbols = [3*ascii_uppercase[i] for i in range(10)]

#     results: dict[str, float] = {}
#     errors: dict[str, Exception] = {}

#     for workers in (1, 2, 5, 10, 20):
#         with timer(f"{workers:>2} workers"):
#             with ThreadPoolExecutor(max_workers=workers) as pool:
#                 futures = {pool.submit(fetch_price, symbol):symbol for symbol in symbols}
#             for f in as_completed(futures.keys()):
#                 try:
#                     results[futures[f]] = f.result()
#                 except ConnectionError as e:
#                     errors[futures[f]] = e
#             for k, v in results.items():
#                 print(f"{k} {v:.3e}")
#             for err in errors.values():
#                 print(err)

    
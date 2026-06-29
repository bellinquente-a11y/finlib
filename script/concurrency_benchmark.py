import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

SLEEP = 0.02

def fetch_price(symbol: str):
    time.sleep(SLEEP)
    return hash(symbol) % 100 + 0.5

async def fetch_price_async(symbol: str):
    await asyncio.sleep(SLEEP)
    return hash(symbol) % 100 + 0.5

symbols = [f"SYM{n}" for n in range(50)]

async def main() -> None:

    start = time.perf_counter()
    for symbol in symbols:
        fetch_price(symbol)
    end = time.perf_counter()
    print(f"{"Sequential":24} {(end-start):.2f}s")

    for workers in [1, 2, 5, 10, 20, 50, 100]:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch_price, symbol) for symbol in symbols]
            for f in as_completed(futures):
                _ = f.result()
        end = time.perf_counter()
        print(f"{f"Threading {workers} workers":24} {(end-start):.2f}s")


    start = time.perf_counter()
    _ = await asyncio.gather(*(fetch_price_async(symbol) for symbol in symbols))
    end = time.perf_counter()
    print(f"{"asyncio":24} {(end-start):.2f}s")

if __name__=="__main__":
    asyncio.run(main())
    # main()


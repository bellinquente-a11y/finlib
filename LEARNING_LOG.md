# Learning log

---

## Week 1, day 1, 15/05/26

### What I built
- pyenv + poetry project scaffold
- a simple vector class using dunder methods

### Surprises
- pyenv and poetry as useful frameworks to project management
- the importance of dunder methods and how they make sense when coding in Python
- what `__repr__`  and `__hash__` do. In particular, why the latter defaults to `None` when it is not defined while `__eq__` is defined

### Still unclear
- how to customise `sys.path`
- how to use pyenv and poetry in practice
- the full use of dunder methods within the language

---

## Week 1, day 2, 18/05

### What I built
- A Trade class using `@dataclass`: reduces boilerplate.
- A Trade class using `Pydantic`: ideal for validation and serialisation
- A test file to be run with `pytest`

### Surprises
- Usefulness of `__slots__` dunder
- Usefulness of `poetry` to fix bugs and clean up the code
- Pydantic's high structure

### Still unclear
- Whether dataclass and Pydantic are used in practice as opposed to numpy arrays

---

## Week 1, day 3, 09/06

### What I built
- A `pydantic.BaseModel` `Portfolio` class of `Trades` with custom dunder methods
- An `Instrument` ABC and two concrete subclasses 
- A Protocol for `Priceable` instruments

### Surprises
- That there is a movement against inheritance and in favour of Protocols (more pythonic)

### Still unclear
- `@runtime_checkable` decorator for Protocols
- how easy it is to keep mypy clean
- how to maintain the `docs` folder

---

## Week 1, day 4 19/06

### What I built
- A **generator** function to lazily stream market data from a csv.
- A **context_manager** timer to time a process.
- A **decorator** to retry a function multiple times in case of exceptions.
- A VWAP calculation function from CSV that fetches the data lazily.

### Surprises
- Iterables and iterators. The standard library allows to avoid reinventing the wheel.
- Generators and the keyword `yield`. How they work. Their usefulness to fetch data lazily.
- Context managers and the `with` keyword. How to build context managers from generators via `@contextlib.contextmanager`

### Still unclear
- Generalised usage of generators.
- How to build test functions.

---

## Week 1, day 5 21/06 - week retrospective

### Deliverables

- pyenv + poetry project
- Vector class (8+ dunder methods)
- Trade model (Pydantic v2, validators, Literal)
- Instrument hierarchy (ABC, abstract methods)
- Priceable Protocol (structural subtyping)
- OHLCV generator (streaming, constant memory)
- Timer context manager
- @retry decorator (exponential backoff)
- Full test suite (>80% coverage)
- GitHub Actions CI (lint -> typecheck -> test)
- Portfolio analysis script

### 3 concepts I now understand
1. dunder methods
2. generators
3. context managers

### What I would design differently
Nothing.

### Python OOP questions that remain unclear
- dataclass vs Pydantic
- usage of protocols

---

## Week 2, day 1 22/06

### What I built
- A utility that groups trades by symbol via `itertools.groupby` and `operator.attrgetter`
- The corresponding print summary function
- A validation decorator for the input of a function

### Surprises
- `pydantic.BaseModel` (`Trade` class) has many useful dunders already coded (`__eq__`, etc.)
- The power of `itertools.groupby` and its `key` input. Remember sorting!!
- The existence of the `operator` functions `attrgetter`, `itemgetter` and `methodcaller`

### Still unclear
- When to use the `operator` methods in practice and whether I will forget about them.

---

## Week 2, day 2 23/06

### What I built
- The fetching module `fetch.py` that simulates fetching data with latency from a network.
- A thread pool via `concurrent.futures.ThreadPoolExecutor` to implement concurrency in I/O operations.
- I timed the fetching of 10 symbols as a function of the number of workers in the pool. Notice the diminishing returns.

| number of workers | processing time |
|--------------------|-----------------|
| 1 | 1.64 |
| 2 | 0.82 |
| 5 | 0.41 |
| 10 | 0.21 |
| 20 | 0.21 |

### Surprises
- Processes vs threads
- Concurrency vs parallelism
- The GIL (global interpreter lock)
- Usefulness of concurrency in I/O operations

### Still unclear
- Exact mechanics of threading

---

## Week 2, day 3 24/06

### What I built
- A simulated data fetcher (using `await asyncio.sleep`) to simulate asynchronous data fetching using the `asyncio` module.
- A real data fetcher applied to Binance data using asynchronous processing via `asyncio`.
- Fetcher has been validated by using a `Pydantic` model at the boundary.
- I compared the timing of the `asyncio` approach (0.16s) vs one implementing with threading via `concurrent.futures.ThreadPoolExecutor` (0.21s).

### Surprises
- How asynchronous (`asyncio` in particular) processing can be very useful for data loading.
- What a *coroutine* and the *event loop* are.
- The subtle difference between threading and asynchronous processing.

### Still unclear
- When to use threading vs asynchronous processing.

---

## Week 2, day 4 25/06

### What I built
- A `TradeRepository` Protocol and its corresponding `InMemoryTradeRepository` implementation (for testing).
- A `PortfolioService` class interfacing with the `TradeRepository` protocol at object creation.
- A `config.py` file returning a `Setting` object from `pydantic_settings.BaseSettings`.
- A `.env` file from which default settings are read.
- Subsettings for Binance API via `pydantic.BaseModel`. 
- Refactor the code to avoid global instantiated dependencies.

### Surprises
- *Repository*: an interface that hides where data actually lives from business logic; the interface is defined as a protocol.
- *Dependency injection*: pass dependencies in via a constructor; not reach out and grab them globally.
- *Environment* and *environment variables* to avoid code changes.

### Still unclear
- How to test different settings, given that the `settings` object is still defined globally.

---

 Week 2, day 5 26/06 - week retrospective

 ### Deliverables
- itertools.groupby trade analytics
- Decorator with arguments (validate_inputs)
- ThreadPoolExecutor fetcher + benchmark
- asyncio + aiohttp fetcher with Pydantic validation
- Repository pattern + DI (Protocol-based)
- pydantic Settings for config
- Vectorised NumPy + chained Pandas cleaning
- End-to-end pipeline, tagged v0.2.0

### 3 concepts I now understand
- how `itertools.groupby` works
- concurrency vs parallelism
- threading as a form of concurrency
- asynchronous processing as a form of concurrency
- the repository pattern and the concept of DI (dependency injection)
- Pandas chaining

### What I would design differently
- `Trades` where to include the sign in the position and notional calculation?

### Questions that remain unclear
- how to test alternative settings

--- 

## Week 3, day 1 26/06

### What I built
- A 3 line drawdown calculation function from a list using `itertools.accumulate`
- A multi-key grouping of Trade objects using `itertools.groupby` (remember sorting first!)
- A `timer` and a `deprecated` decorator with tests.

### Surprises
- How quick is the drawdown calculation with `itertools`
- How powerful is `groupby`

---

## Week 3, day 2 

### What I built
- I added `structlog.log` to the `fetch.py` module.
- Wrote a benchmark script comparing sequential, threading and async. Results below. Conceptual discussion in [concurrency_benchmark.md](./docs/concurrency_benchmark.md).

| process type | processing time |
|-|-|
| Sequential | 1.16s |
| Threading 1 workers | 1.16s |
| Threading 2 workers | 0.57s |
| Threading 5 workers | 0.23s |
| Threading 10 workers | 0.13s |
| Threading 20 workers | 0.08s |
| Threading 50 workers | 0.03s |
| Threading 100 workers | 0.03s |
| asyncio | 0.02s |

### Surprises
- How beautiful the output of `structlog` looks.
- Preemptive vs cooperational concurrency (i.e., threading vs async).
- Async runs on one thread.

### Still unclear
- The mechanical details of threads, processes, etc.

# Comparing sequential, threading and asynchronous processing

The script `concurrency_benchmark.py` processes 50 times the same function with different processing approaches.
The function simulates a fixed latency.

1. Sequential is obviously the slowest: each iteration waits until the previous function was run to start a new one.

2. Threading speeds up the calculation, provided an adequate number of `max_workers`. When the latter is higher than 1, different threads run concurrently. This allows a new function to be started before the previous one has finished. 

3. With threading, the CPU manages the rotation among different threads concurrently. The number of workers reflects the number of concurrent threads. In the trivial case of 1 worker, only one thread is run in the concurrency pool; this is equivalent to sequential processing. With 2 max workers, the CPU rotated among 2 threads. This means that before the 1st call ends, the 2nd can be called via a second thread; however, the 3rd cannot due to the limit on workers. When the max workers is set to 50, all function calls can be started before any of them ends. Clearly, adding further workers does not speed up the calculation, as there are no further function calls required. 

4. While threading is **preemptive** (the CPU switches among threads at any time), asynchronous processing is **cooperative** (the coroutines alternate processing at specific points established in the code).

5. In this example asynchronous processing compares (and is slightly faster) than the fastest threading approach. The former optimises explicitly what the latter does implicitly (via rotation among threads). In both cases, waiting time is used efficiently: in the former case by passing to another coroutine; in the latter by rotating among threads. I suspect that asynchronous processing is slightly faster because the latter runs on a single thread in user space, avoiding the overhead associated to creating multiple threads. This is the typical case for I/O bound work. For CPU-bound Python processing, neither threading nor async scales: multiprocessing is likely the best tool.
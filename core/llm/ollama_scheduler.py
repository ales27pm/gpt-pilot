from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field


@dataclass(order=True)
class OllamaJob:
    """Represents a job executed via an Ollama model."""

    priority: int
    prompt: str = field(compare=False, default="")
    model: str = field(compare=False, default="")
    cpu_threads: int = field(compare=False, default=1)
    gpu_mem_mb: int = field(compare=False, default=1)
    sleep_ms: int = field(compare=False, default=0)
    _future: asyncio.Future[str] = field(init=False, repr=False, compare=False)
    _done: asyncio.Event = field(init=False, repr=False, compare=False)


class WeightedSemaphore:
    """Semaphore that allows acquiring multiple units at once."""

    def __init__(self, value: int) -> None:
        self.sem = asyncio.Semaphore(value)

    async def acquire(self, n: int) -> None:
        for _ in range(n):
            await self.sem.acquire()

    def release(self, n: int) -> None:
        for _ in range(n):
            self.sem.release()


class OllamaScheduler:
    """Cooperative scheduler for CPU/GPU bound Ollama jobs.

    Jobs are executed in two phases: a CPU preprocessing stage followed by a
    GPU inference stage.  CPU threads are managed by a standard semaphore while
    GPU memory is tracked via a weighted semaphore so multiple jobs can share
    the GPU concurrently as long as sufficient memory is available.
    """

    def __init__(self, total_cpu_threads: int, total_gpu_mem: int) -> None:
        self.total_cpu_threads = total_cpu_threads
        self.total_gpu_mem = total_gpu_mem
        self._cpu_sem = asyncio.Semaphore(total_cpu_threads)
        self._gpu_ws = WeightedSemaphore(total_gpu_mem)
        self._queue: asyncio.PriorityQueue[OllamaJob] = asyncio.PriorityQueue()
        self.completed: list[OllamaJob] = []
        self._gpu_active = 0
        self.max_gpu_concurrency = 0

    @property
    def cpu_free(self) -> int:
        return self._cpu_sem._value

    @property
    def gpu_mem_free(self) -> int:
        return self._gpu_ws.sem._value

    async def submit(self, job: OllamaJob) -> str:
        """Submit a job and wait for its completion."""

        if job.cpu_threads < 0 or job.gpu_mem_mb < 0:
            raise ValueError("cpu_threads and gpu_mem_mb must be non-negative")
        if not isinstance(job.prompt, str) or not job.prompt:
            raise ValueError("prompt must be a non-empty string")
        if job.cpu_threads > self.total_cpu_threads or job.gpu_mem_mb > self.total_gpu_mem:
            raise ValueError("Requested resources exceed scheduler limits")

        loop = asyncio.get_running_loop()
        job._future = loop.create_future()
        job._done = asyncio.Event()
        await self._queue.put(job)
        # start worker to process queue
        asyncio.create_task(self._worker())
        try:
            return await job._future
        except asyncio.CancelledError:
            job._future.cancel()
            await job._done.wait()
            raise

    async def _worker(self) -> None:
        while not self._queue.empty():
            job: OllamaJob = await self._queue.get()

            # CPU phase
            await self._cpu_sem.acquire()
            try:
                await asyncio.sleep(0)  # Simulate CPU bound work
            finally:
                self._cpu_sem.release()

            if job._future.cancelled():
                job._done.set()
                continue

            # GPU phase
            await self._gpu_ws.acquire(job.gpu_mem_mb)
            self._gpu_active += 1
            self.max_gpu_concurrency = max(self.max_gpu_concurrency, self._gpu_active)
            sleep_task = asyncio.create_task(asyncio.sleep(job.sleep_ms / 1000))
            try:
                await asyncio.wait({sleep_task, job._future}, return_when=asyncio.FIRST_COMPLETED)
                if not job._future.cancelled():
                    self.completed.append(job)
                    job._future.set_result(job.prompt)
            finally:
                sleep_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await sleep_task
                self._gpu_active -= 1
                self._gpu_ws.release(job.gpu_mem_mb)
                job._done.set()


__all__ = ["OllamaJob", "OllamaScheduler", "WeightedSemaphore"]

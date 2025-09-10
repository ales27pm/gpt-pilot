from __future__ import annotations

import asyncio
import heapq
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(order=True)
class OllamaJob:
    """Represents a job executed via an Ollama model.

    The dataclass is orderable by ``priority`` so it can be stored in a
    priority queue.  Lower ``priority`` values represent more important jobs.
    """

    priority: int
    prompt: str = field(compare=False, default="")
    model: str = field(compare=False, default="")
    cpu_threads: int = field(compare=False, default=1)
    gpu_mem_mb: int = field(compare=False, default=0)
    _future: asyncio.Future[str] = field(init=False, repr=False, compare=False)


class OllamaScheduler:
    """Cooperative scheduler for CPU/GPU bound Ollama jobs.

    The scheduler tracks available CPU threads and GPU memory and executes
    jobs in two stages: a CPU preprocessing phase followed by a GPU inference
    phase.  Multiple GPU jobs may run concurrently so long as sufficient memory
    is available.  The implementation is intentionally lightweight but includes
    error handling and resource accounting to remain robust during testing.
    """

    def __init__(self, total_cpu_threads: int, total_gpu_mem: int) -> None:
        self.total_cpu_threads = total_cpu_threads
        self.total_gpu_mem = total_gpu_mem
        self.cpu_free = total_cpu_threads
        self.gpu_mem_free = total_gpu_mem
        self._cpu_queue: asyncio.PriorityQueue[OllamaJob] = asyncio.PriorityQueue()
        self._gpu_queue: List[OllamaJob] = []  # heapq based priority queue
        self._gpu_running: List[OllamaJob] = []
        self.max_gpu_concurrency = 0
        self.completed: list[OllamaJob] = []
        self._lock = asyncio.Lock()

    async def submit(self, job: OllamaJob) -> str:
        """Submit a job and wait for its completion."""

        job._future = asyncio.get_event_loop().create_future()
        await self._cpu_queue.put(job)
        async with self._lock:
            await self._schedule()
        return await job._future

    async def _schedule(self) -> None:
        """Run scheduling loops for CPU and GPU queues."""

        made_progress = True
        while made_progress:
            made_progress = False

            # CPU scheduling: start preprocessing for jobs that fit available CPU
            while not self._cpu_queue.empty():
                job = await self._cpu_queue.get()
                if job.cpu_threads <= self.cpu_free:
                    self.cpu_free -= job.cpu_threads
                    asyncio.create_task(self._run_preprocess(job))
                    made_progress = True
                else:
                    await self._cpu_queue.put(job)
                    break

            # GPU scheduling
            while self._gpu_queue and self._gpu_queue[0].gpu_mem_mb <= self.gpu_mem_free:
                job = heapq.heappop(self._gpu_queue)
                self.gpu_mem_free -= job.gpu_mem_mb
                asyncio.create_task(self._run_gpu(job))
                made_progress = True

    async def _run_preprocess(self, job: OllamaJob) -> None:
        try:
            await asyncio.sleep(0)  # Simulate CPU bound work
        finally:
            self.cpu_free += job.cpu_threads
            async with self._lock:
                heapq.heappush(self._gpu_queue, job)
                await self._schedule()
    async def _run_gpu(self, job: OllamaJob) -> None:
        self._gpu_running.append(job)
        self.max_gpu_concurrency = max(self.max_gpu_concurrency, len(self._gpu_running))
        try:
            await asyncio.sleep(0)  # Simulate GPU inference
        finally:
            self.gpu_mem_free += job.gpu_mem_mb
            self._gpu_running.remove(job)
            self.completed.append(job)
            job._future.set_result(job.prompt)
            async with self._lock:
                await self._schedule()


__all__ = ["OllamaJob", "OllamaScheduler"]

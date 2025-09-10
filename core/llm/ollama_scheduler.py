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
        """
        Initialize an OllamaScheduler with the given CPU thread and GPU memory resources.
        
        Parameters:
            total_cpu_threads (int): Total number of CPU threads available for preprocessing.
            total_gpu_mem (int): Total GPU memory (in MB) available for concurrent inference jobs.
        
        Initializes scheduler state:
            - cpu_free, gpu_mem_free: current available CPU threads and GPU memory.
            - _cpu_queue: priority queue for CPU preprocessing jobs.
            - _gpu_queue: heap-based priority queue for jobs ready for GPU inference.
            - _gpu_running: list of currently running GPU jobs.
            - max_gpu_concurrency: peak number of concurrent GPU jobs observed.
            - completed: list of completed jobs.
            - _lock: asyncio.Lock protecting scheduler state.
        """
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
        """
        Submit an OllamaJob for processing and wait for its completion.
        
        The job is enqueued for CPU preprocessing, then scheduled for GPU work when resources permit.
        A Future is created on the job (job._future) and will be completed with the final prompt string when the job finishes.
        
        Parameters:
            job (OllamaJob): The job to submit. Its internal Future (job._future) will be created by this method and resolved with the job's resulting prompt.
        
        Returns:
            str: The final prompt/result produced for the job (the value set on job._future) after GPU processing completes.
        """

        job._future = asyncio.get_event_loop().create_future()
        await self._cpu_queue.put(job)
        async with self._lock:
            await self._schedule()
        return await job._future

    async def _schedule(self) -> None:
        """
        Run the scheduler loop that allocates available CPU threads and GPU memory to queued jobs.
        
        This method repeatedly attempts to make progress until no more jobs can be started:
        - CPU phase: dequeues highest-priority jobs from self._cpu_queue and, if enough cpu_free is available, deducts cpu threads and starts preprocessing in a background task. If a job requires more CPU than currently free it is re-queued and CPU scheduling for this cycle stops.
        - GPU phase: pops jobs from the heap-based self._gpu_queue whose gpu_mem_mb fits into gpu_mem_free, deducts GPU memory, and starts GPU execution in a background task.
        
        The loop ends when neither phase can start any additional jobs. The method does not wait for the background tasks to finish; those tasks are responsible for releasing resources and re-invoking scheduling.
        """

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
        """
        Release CPU resources for a completed preprocessing job and move it to the GPU queue.
        
        This coroutine represents the completion of a job's CPU-bound preprocessing step. It frees the CPU threads previously allocated to the job, pushes the job onto the scheduler's GPU priority queue, and triggers the scheduler to reconsider work distribution.
        
        Parameters:
            job (OllamaJob): The job whose preprocessing has finished; will be enqueued for GPU inference.
        
        """
        try:
            await asyncio.sleep(0)  # Simulate CPU bound work
        finally:
            self.cpu_free += job.cpu_threads
            async with self._lock:
                heapq.heappush(self._gpu_queue, job)
                await self._schedule()
    async def _run_gpu(self, job: OllamaJob) -> None:
        """
        Run the GPU/inference phase for a job and finalize it.
        
        Performs the GPU-bound portion of a job: marks the job as running (updating internal concurrency tracking), awaits the GPU work (simulated), then on completion releases GPU memory, removes the job from the running set, records it as completed, and sets the job's future result to the job's prompt. Finally it reacquires the scheduler lock and triggers another scheduling pass.
        
        Parameters:
            job (OllamaJob): The job whose GPU phase should be executed. This function sets job._future with the final result and mutates scheduler state (gpu_mem_free, _gpu_running, completed, max_gpu_concurrency).
        """
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

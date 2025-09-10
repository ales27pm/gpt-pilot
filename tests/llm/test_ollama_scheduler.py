import asyncio

import pytest

from core.llm.ollama_scheduler import OllamaJob, OllamaScheduler


@pytest.mark.asyncio
async def test_scheduler_runs_jobs_and_frees_resources():
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)
    job1 = OllamaJob(priority=0, prompt="job1", cpu_threads=1, gpu_mem_mb=1)
    job2 = OllamaJob(priority=1, prompt="job2", cpu_threads=1, gpu_mem_mb=1)

    results = await asyncio.gather(scheduler.submit(job1), scheduler.submit(job2))

    assert results == ["job1", "job2"]
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem
    assert scheduler.completed[0] is job1


@pytest.mark.asyncio
async def test_scheduler_runs_gpu_jobs_concurrently():
    scheduler = OllamaScheduler(total_cpu_threads=3, total_gpu_mem=2)
    job1 = OllamaJob(priority=0, prompt="job1", cpu_threads=1, gpu_mem_mb=1)
    job2 = OllamaJob(priority=1, prompt="job2", cpu_threads=1, gpu_mem_mb=1)
    job3 = OllamaJob(priority=2, prompt="job3", cpu_threads=1, gpu_mem_mb=1)

    results = await asyncio.gather(
        scheduler.submit(job1),
        scheduler.submit(job2),
        scheduler.submit(job3),
    )

    assert set(results) == {"job1", "job2", "job3"}
    # GPU should have processed at least two jobs at once
    assert scheduler.max_gpu_concurrency >= 2
    # High priority jobs should complete before the lowest priority one
    completed_prompts = [job.prompt for job in scheduler.completed]
    assert set(completed_prompts[:2]) == {"job1", "job2"}
    assert completed_prompts[-1] == "job3"
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

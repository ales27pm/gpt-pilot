import asyncio

import pytest

from core.llm.ollama_scheduler import OllamaJob, OllamaScheduler


@pytest.mark.asyncio
async def test_scheduler_runs_jobs_and_frees_resources():
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)
    # Submit low priority job first to ensure priority scheduling works
    job2 = OllamaJob(priority=1, prompt="job2", cpu_threads=1, gpu_mem_mb=1)
    job1 = OllamaJob(priority=0, prompt="job1", cpu_threads=1, gpu_mem_mb=1)

    t_low = asyncio.create_task(scheduler.submit(job2))
    t_high = asyncio.create_task(scheduler.submit(job1))
    results = await asyncio.gather(t_low, t_high)

    assert set(results) == {"job1", "job2"}
    # High priority job should complete first
    assert scheduler.completed[0] is job1
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem


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
    assert scheduler.max_gpu_concurrency >= 2
    completed_prompts = [job.prompt for job in scheduler.completed]
    assert completed_prompts[0] == "job1"
    assert completed_prompts[1] == "job2"
    assert completed_prompts[-1] == "job3"
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem


@pytest.mark.asyncio
async def test_scheduler_rejects_invalid_requests():
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)
    with pytest.raises(ValueError):
        await scheduler.submit(OllamaJob(priority=0, prompt="bad", cpu_threads=0, gpu_mem_mb=1))
    with pytest.raises(ValueError):
        await scheduler.submit(OllamaJob(priority=0, prompt="bad", cpu_threads=1, gpu_mem_mb=-1))
    with pytest.raises(ValueError):
        await scheduler.submit(OllamaJob(priority=0, prompt="bad", cpu_threads=3, gpu_mem_mb=1))
    with pytest.raises(ValueError):
        await scheduler.submit(OllamaJob(priority=0, prompt="bad", cpu_threads=1, gpu_mem_mb=3))


@pytest.mark.asyncio
async def test_scheduler_handles_many_jobs():
    scheduler = OllamaScheduler(total_cpu_threads=4, total_gpu_mem=4)
    jobs = [OllamaJob(priority=i % 3, prompt=f"job{i}", cpu_threads=1, gpu_mem_mb=1) for i in range(10)]

    results = await asyncio.gather(*(scheduler.submit(job) for job in jobs))

    assert set(results) == {f"job{i}" for i in range(10)}
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem
    # Ensure jobs completed in non-decreasing priority order
    priorities = [job.priority for job in scheduler.completed]
    assert priorities == sorted(priorities)

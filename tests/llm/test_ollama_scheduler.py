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




























    # Ensure jobs completed in non-decreasing priority order
    priorities = [job.priority for job in scheduler.completed]
    assert priorities == sorted(priorities)

# Additional comprehensive tests for OllamaScheduler
# Testing framework: pytest with pytest-asyncio style markers already used in this project.

import time

@pytest.mark.asyncio
async def test_scheduler_respects_cpu_capacity_when_gpu_is_plenty():
    # 1 CPU thread total, but multiple GPU mem available; ensure CPU limits concurrency.
    scheduler = OllamaScheduler(total_cpu_threads=1, total_gpu_mem=10)
    job1 = OllamaJob(priority=0, prompt="c1", cpu_threads=1, gpu_mem_mb=1)
    job2 = OllamaJob(priority=0, prompt="c2", cpu_threads=1, gpu_mem_mb=1)
    job3 = OllamaJob(priority=0, prompt="c3", cpu_threads=1, gpu_mem_mb=1)

    results = await asyncio.gather(
        scheduler.submit(job1),
        scheduler.submit(job2),
        scheduler.submit(job3),
    )

    assert set(results) == {"c1", "c2", "c3"}
    # Only one CPU thread available, so CPU concurrency should never exceed 1 if tracked
    if hasattr(scheduler, "max_cpu_concurrency"):
        assert scheduler.max_cpu_concurrency <= 1
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

@pytest.mark.asyncio
async def test_scheduler_rejects_job_exceeding_total_resources():
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=1024)
    too_big_cpu = OllamaJob(priority=0, prompt="too_cpu", cpu_threads=3, gpu_mem_mb=256)
    too_big_gpu = OllamaJob(priority=0, prompt="too_gpu", cpu_threads=1, gpu_mem_mb=2048)

    # Expect an exception or immediate failure for oversize jobs; handle both behaviors gracefully
    with pytest.raises(Exception):
        await scheduler.submit(too_big_cpu)
    with pytest.raises(Exception):
        await scheduler.submit(too_big_gpu)

    # Resources should remain fully free after rejection
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

@pytest.mark.asyncio
async def test_scheduler_zero_resource_job_executes_and_cleans_up():
    # A job that nominally doesn't consume resources (if supported) should still run.
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2048)
    zero_job = OllamaJob(priority=0, prompt="zero", cpu_threads=0, gpu_mem_mb=0)
    res = await scheduler.submit(zero_job)
    assert res == "zero"
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem
    assert scheduler.completed[-1] is zero_job

@pytest.mark.asyncio
async def test_scheduler_priority_ordering_with_contention():
    # Create contention on both CPU and GPU to verify strict priority.
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)
    high1 = OllamaJob(priority=0, prompt="high1", cpu_threads=1, gpu_mem_mb=1)
    high2 = OllamaJob(priority=0, prompt="high2", cpu_threads=1, gpu_mem_mb=1)
    low1 = OllamaJob(priority=5, prompt="low1", cpu_threads=1, gpu_mem_mb=1)
    low2 = OllamaJob(priority=10, prompt="low2", cpu_threads=1, gpu_mem_mb=1)

    results = await asyncio.gather(
        scheduler.submit(low2),
        scheduler.submit(low1),
        scheduler.submit(high2),
        scheduler.submit(high1),
    )

    assert set(results) == {"high1", "high2", "low1", "low2"}
    completed_prompts = [j.prompt for j in scheduler.completed]
    # The first two to finish must be the high-priority ones (lower number = higher priority)
    assert set(completed_prompts[:2]) == {"high1", "high2"}
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

@pytest.mark.asyncio
async def test_scheduler_handles_cancellation_and_releases_resources():
    # Submit a job and cancel it; resources must be returned and job not counted as completed.
    scheduler = OllamaScheduler(total_cpu_threads=1, total_gpu_mem=1)
    long_job = OllamaJob(priority=0, prompt="long", cpu_threads=1, gpu_mem_mb=1, sleep_ms=300) if hasattr(OllamaJob, "sleep_ms") else OllamaJob(priority=0, prompt="long", cpu_threads=1, gpu_mem_mb=1)

    # Fire off the task and cancel shortly after
    task = asyncio.create_task(scheduler.submit(long_job))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Resources should be free; job should not be in completed list
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem
    assert all(j is not long_job for j in scheduler.completed)

@pytest.mark.asyncio
async def test_scheduler_many_small_gpu_jobs_hit_gpu_concurrency():
    # Ensure GPU concurrency tracking reflects parallelism under sufficient CPU.
    scheduler = OllamaScheduler(total_cpu_threads=8, total_gpu_mem=8)
    jobs = [OllamaJob(priority=i, prompt=f"g{i}", cpu_threads=1, gpu_mem_mb=1) for i in range(8)]
    results = await asyncio.gather(*(scheduler.submit(j) for j in jobs))
    assert set(results) == {f"g{i}" for i in range(8)}
    if hasattr(scheduler, "max_gpu_concurrency"):
        assert scheduler.max_gpu_concurrency >= 2
        assert scheduler.max_gpu_concurrency <= 8
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

@pytest.mark.asyncio
async def test_scheduler_serializes_when_gpu_is_bottleneck():
    # Plenty of CPU but GPU mem = 1, forcing serialization by GPU.
    scheduler = OllamaScheduler(total_cpu_threads=4, total_gpu_mem=1)
    j1 = OllamaJob(priority=0, prompt="s1", cpu_threads=1, gpu_mem_mb=1)
    j2 = OllamaJob(priority=0, prompt="s2", cpu_threads=1, gpu_mem_mb=1)
    j3 = OllamaJob(priority=0, prompt="s3", cpu_threads=1, gpu_mem_mb=1)
    await asyncio.gather(
        scheduler.submit(j1),
        scheduler.submit(j2),
        scheduler.submit(j3),
    )
    if hasattr(scheduler, "max_gpu_concurrency"):
        assert scheduler.max_gpu_concurrency == 1
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem

@pytest.mark.asyncio
async def test_scheduler_invalid_inputs_raise_meaningful_errors():
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)

    # Negative resources should raise
    with pytest.raises(Exception):
        await scheduler.submit(OllamaJob(priority=0, prompt="neg_cpu", cpu_threads=-1, gpu_mem_mb=0))
    with pytest.raises(Exception):
        await scheduler.submit(OllamaJob(priority=0, prompt="neg_gpu", cpu_threads=0, gpu_mem_mb=-1))

    # Non-string prompt or missing prompt should raise (if validated)
    try:
        invalid_job = OllamaJob(priority=0, prompt=None, cpu_threads=1, gpu_mem_mb=1)  # type: ignore[arg-type]
        with pytest.raises(Exception):
            await scheduler.submit(invalid_job)
    except TypeError:
        # Dataclass/type validation may throw on construction; that's acceptable.
        pass

@pytest.mark.asyncio
async def test_scheduler_completes_and_tracks_order_of_equal_priority():
    # When priorities are equal, ensure FIFO or stable handling if defined; we at least assert all results returned.
    scheduler = OllamaScheduler(total_cpu_threads=2, total_gpu_mem=2)
    j1 = OllamaJob(priority=1, prompt="e1", cpu_threads=1, gpu_mem_mb=1)
    j2 = OllamaJob(priority=1, prompt="e2", cpu_threads=1, gpu_mem_mb=1)
    j3 = OllamaJob(priority=1, prompt="e3", cpu_threads=1, gpu_mem_mb=1)

    results = await asyncio.gather(
        scheduler.submit(j1),
        scheduler.submit(j2),
        scheduler.submit(j3),
    )
    assert set(results) == {"e1", "e2", "e3"}
    # Best-effort stability: first two completed should be from first two enqueued
    completed_prompts = [j.prompt for j in scheduler.completed]
    assert set(completed_prompts[:2]).issubset({"e1", "e2"})
    assert scheduler.cpu_free == scheduler.total_cpu_threads
    assert scheduler.gpu_mem_free == scheduler.total_gpu_mem
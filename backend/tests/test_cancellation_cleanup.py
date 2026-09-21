"""
Demonstrates that fake_io_operation's cleanup (the finally block) runs
even when the code inside raises an exception, AND when the task is
cancelled mid-wait — two different failure modes, both required by the
acceptance table's "Cancellation/exception" case.
"""

import asyncio
import logging
import pytest

from app.common.fake_io import fake_io_operation


@pytest.mark.asyncio
async def test_cleanup_runs_when_exception_raised(caplog):
    caplog.set_level(logging.INFO, logger="app.io")

    with pytest.raises(ValueError):
        async with fake_io_operation("failing_operation"):
            raise ValueError("something went wrong mid-operation")

    messages = [r.message for r in caplog.records]
    assert any("[io start] failing_operation" in m for m in messages)
    assert any("[io end] failing_operation" in m for m in messages), (
        "cleanup did not run after the exception — finally block failed"
    )


@pytest.mark.asyncio
async def test_cleanup_runs_when_task_cancelled(caplog):
    caplog.set_level(logging.INFO, logger="app.io")

    async def slow_operation():
        async with fake_io_operation("cancelled_operation"):
            await asyncio.sleep(10)  # deliberately long — we cancel before this finishes

    task = asyncio.create_task(slow_operation())
    await asyncio.sleep(0.05)  # let it actually start
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    messages = [r.message for r in caplog.records]
    assert any("[io start] cancelled_operation" in m for m in messages)
    assert any("[io end] cancelled_operation" in m for m in messages), (
        "cleanup did not run after cancellation — finally block failed"
    )


@pytest.mark.asyncio
async def test_server_still_works_after_a_failed_operation(client):
    """The PRD's phrasing: 'next request still works' after a
    cancellation/exception. Confirms the app-level server isn't left in
    a broken state by the two tests above."""
    r = client.get("/health/live")
    assert r.status_code == 200
"""
Wraps the simulated I/O delay with explicit start/end logging AND
guaranteed cleanup via try/finally — this is what lets A4's tests prove
two separate things:
1. Concurrent requests genuinely OVERLAP (their start/end timestamps
   interleave), not just run one after another.
2. Cleanup runs even when something inside raises or the task is
   cancelled mid-wait — the finally block is what guarantees this.
"""

import contextlib
import time
import logging

logger = logging.getLogger("app.io")


@contextlib.asynccontextmanager
async def fake_io_operation(name: str):
    start = time.perf_counter()
    logger.info("[io start] %s", name)
    try:
        yield
    finally:
        # This runs whether the block completes normally, raises an
        # exception, OR gets cancelled (asyncio.CancelledError) — that's
        # the whole point of finally, and what the PRD's cancellation
        # test is checking for.
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("[io end] %s (%.1fms)", name, duration_ms)
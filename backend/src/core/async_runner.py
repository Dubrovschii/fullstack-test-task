"""Run coroutines from synchronous Celery tasks on one long-lived event loop.

asyncpg connections are bound to the loop that created them, so every task in a
worker process must run on the same loop.  ``asyncio.Runner`` keeps that loop
alive between calls (the previous code did this by hand with a module global).
"""

import asyncio
from collections.abc import Coroutine
from typing import Any

_runner: asyncio.Runner | None = None


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    global _runner
    if _runner is None:
        _runner = asyncio.Runner()
    return _runner.run(coroutine)

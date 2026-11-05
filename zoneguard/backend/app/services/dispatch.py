"""Background work execution (analysis jobs, notification delivery).

A bounded ThreadPoolExecutor keeps the pilot single-process. ``inline`` mode runs work
synchronously (used by tests). For scale-out, swap for a durable queue (documented).
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

log = logging.getLogger("zoneguard.dispatch")

_executor: ThreadPoolExecutor | None = None
_inline = False


def configure(workers: int = 2, inline: bool = False) -> None:
    global _executor, _inline
    _inline = inline
    if not inline and _executor is None:
        _executor = ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="zg-worker")


def submit(fn: Callable, *args, **kwargs) -> None:
    def _run():
        try:
            fn(*args, **kwargs)
        except Exception:  # noqa: BLE001 - background errors must be logged, never lost
            log.exception("background task %s failed", getattr(fn, "__name__", fn))

    if _inline or _executor is None:
        _run()
    else:
        _executor.submit(_run)


def shutdown() -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=True)
        _executor = None

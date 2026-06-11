"""
PhotoSync — shared thread-pool executors for CPU-bound tasks.

Using a single executor avoids redundant thread pools across modules.
"""

from concurrent.futures import ThreadPoolExecutor

_IO_EXECUTOR: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ps-io")
_THUMB_EXECUTOR: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ps-thumb")


def get_io_executor() -> ThreadPoolExecutor:
    return _IO_EXECUTOR


def get_thumb_executor() -> ThreadPoolExecutor:
    return _THUMB_EXECUTOR


async def shutdown_executors() -> None:
    """Gracefully shut down all executors (call on app shutdown)."""
    for ex in (_IO_EXECUTOR, _THUMB_EXECUTOR):
        ex.shutdown(wait=True, cancel_futures=True)

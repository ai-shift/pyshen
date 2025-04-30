"""
From https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
"""

import asyncio
from asyncio import AbstractEventLoop
from asyncio import Future as AFuture
from collections.abc import Awaitable
from concurrent.futures import Future
from threading import Thread


def create_event_loop_thread() -> AbstractEventLoop:
    def start_background_loop(loop: AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    eventloop = asyncio.new_event_loop()
    thread = Thread(target=start_background_loop, args=(eventloop,), daemon=True)
    thread.start()
    return eventloop


def run_coro_in_thread[T](
    coro: AFuture[T] | Awaitable[T], loop: None | AbstractEventLoop = None
) -> Future[T]:
    if loop is None:
        loop = create_event_loop_thread()
    return asyncio.run_coroutine_threadsafe(coro, loop)

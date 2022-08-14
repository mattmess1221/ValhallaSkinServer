from typing import AsyncIterable, AsyncIterator, Callable, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def camel_case(s: str) -> str:
    parts = s.split("_")
    parts[1:] = [_.capitalize() for _ in parts[1:]]
    return "".join(parts)


async def alist(iterable: AsyncIterable[T]) -> list[T]:
    return [x async for x in iterable]


async def aislice(iterable: AsyncIterable[T], limit: int | None) -> AsyncIterator[T]:
    count = 0
    async for item in iterable:
        if limit is not None and count >= limit:
            break
        yield item
        count += 1


async def agroupby(
    iterable: AsyncIterable[T], key: Callable[[T], K]
) -> AsyncIterator[tuple[K, AsyncIterator[T]]]:
    iterator = iterable.__aiter__()
    try:
        item = await iterator.__anext__()
    except StopAsyncIteration:
        return

    async def getvalues() -> AsyncIterator[T]:
        nonlocal item
        yield item
        while True:
            try:
                item = await iterator.__anext__()
            except StopAsyncIteration:
                item = None
                break
            else:
                if keyvalue != key(item):
                    break
                yield item

    while item is not None:
        keyvalue = key(item)
        yield keyvalue, getvalues()

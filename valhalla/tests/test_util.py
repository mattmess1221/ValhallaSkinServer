from operator import itemgetter

import pytest

from ..util import agroupby, aislice, camel_case


@pytest.mark.parametrize(
    "a, b",
    [
        ("hello_world", "helloWorld"),
        ("python", "python"),
        ("", ""),
    ],
)
def test_camel_case(a, b):
    assert camel_case(a) == b


async def acounter(start=0, end=None, step=1):
    value = start
    while end is None or value < end:
        yield value
        value += step


@pytest.mark.anyio
@pytest.mark.parametrize(
    ["iterable", "limit", "result"],
    [
        [acounter(), 10, list(range(10))],
        [acounter(end=10), 20, list(range(10))],
        [acounter(), 0, list()],
    ],
)
async def test_aislice(iterable, limit, result):
    assert [x async for x in aislice(iterable, limit)] == result


@pytest.mark.anyio
@pytest.mark.parametrize(
    ["groups", "values"],
    [
        ["abc", list(range(3))],
        ["", ""],
    ],
)
async def test_groupby(groups, values):
    async def grouped_collection():
        for t in groups:
            for v in values:
                yield {"type": t, "value": v}

    def grouped_dict():
        return {t: [v for v in values] for t in groups}

    grouped = {
        key: [v["value"] async for v in values]
        async for key, values in agroupby(grouped_collection(), key=itemgetter("type"))
    }

    assert grouped == grouped_dict()

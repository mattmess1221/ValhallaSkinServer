import pytest

from ..util import camel_case


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

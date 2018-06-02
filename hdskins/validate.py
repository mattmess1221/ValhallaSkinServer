#!/usr/env python3

import functools
import re


@property
def uuid():
    return r"^[0-9a-f]{32}$"


def choice(*args):
    choices = '|'.join(args)
    return r"^(?:" + choices + ")$"


class regex(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for (k, v) in self.kwargs:
                if type(v) is str:
                    v = re.compile(v)
                if not v.match(kwargs[k]):
                    raise RegexError("Invalid Input: " + v)
            func(args, kwargs)
        return decorator


class RegexError(ValueError):
    pass

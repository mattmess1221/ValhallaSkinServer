#!/usr/env python3

import functools
import re

uuid = r"^[0-9a-f]{32}$"


def choice(*args):
    choices = '|'.join(args)
    return r"^(?:" + choices + ")$"


def regex(**regs):

    def callable(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for k, v in regs.items():
                reg = re.compile(v)
                if not reg.match(kwargs[k]):
                    raise ValueError("Invalid Input: " + kwargs[k])
            return func(*args, **kwargs)
        return decorator
    return callable

#!/usr/env python3

import functools
import re


class regex:
    UUID = r"^[0-9a-f]{32}$"

    def __init__(self, **regs):
        self.regs = regs

    def __call__(self, func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            for k, v in self.regs.items():
                reg = re.compile(v)
                if not reg.match(kwargs[k]):
                    raise ValueError("Invalid Input: " + kwargs[k])
            return func(*args, **kwargs)

        return decorator


def noneof(*args):
    return r"^(?!^(?:%s)$).+$" % '|'.join(args)

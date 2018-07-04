#!/usr/env python3

import functools
import re


class regex(**regs):

    UUID = r"^[0-9a-f]{32}$"

    @staticmethod
    def choice(*args):
        choices = '|'.join(args)
        return r"^(?:" + choices + ")$"

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

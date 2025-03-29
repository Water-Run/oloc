r"""
:author: WaterRun
:date: 2025-03-29
:file: oloc_parser.py
:description: Oloc parser
"""

from oloc_token import Token
from oloc_exceptions import *
import time


class Unit:
    r"""
    运算体单元
    """


class Parser:
    r"""
    语法分析器
    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.hierarchy: list[int] = [0 for _ in tokens]
        self.time_cost = -1

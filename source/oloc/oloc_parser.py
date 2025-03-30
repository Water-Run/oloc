r"""
:author: WaterRun
:date: 2025-03-30
:file: oloc_parser.py
:description: Oloc parser
"""

import time

from oloc_token import Token
from enum import Enum


class Unit:
    r"""
    运算体单元
    """

    class TYPE(Enum):
        r"""
        运算体单元类型
        """
        BIN_EXP = 'BinaryExpression'
        LITERAL = 'Literal'
        FUN_CAL = 'FunctionCall'
        GRP_EXP = 'GroupExpression'

    def __init__(self, unit_type: TYPE, token_flow=list[Token]):
        self.type = unit_type
        self.flow = token_flow
        self.sub: list[Unit] = []

    def __repr__(self):
        result = (f"Unit: {self.type}\n"
                  f"{self.flow}\n"
                  f"{len(self.sub)} sub(s): ")
        for index, temp_sub in self.sub:
            result += f"Sub {index}: "
            result += str(temp_sub)
        return result


class Parser:
    r"""
    语法分析器
    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.units: list[Unit] = []
        self.time_cost = -1

    def _build(self):
        r"""
        生成Unit流
        :return: None
        """
        LITERAL = (
            Token.TYPE.INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.LONG_CUSTOM,
        )
        for token_index, temp_token in enumerate(self.tokens):
            ...


    def _syntax_check(self):
        r"""
        语法检查
        :return: None
        """

    def execute(self):
        r"""
        执行语法分析
        :return: None
        """
        start_time = time.time_ns()
        self._build()
        self._syntax_check()
        self.time_cost = time.time_ns() - start_time

r"""
:author: WaterRun
:date: 2025-04-03
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

import time

from oloc_token import Token
from oloc_lexer import Lexer
from oloc_ast import ASTTree, ASTNode
from oloc_exceptions import *


class Number:
    r"""
    数字单元
    """

    class TYPE(Enum):

        RATIONAL = "ral"
        IRRATIONAL = 'irr'

    def __init__(self, token: Token, number_type: TYPE):
        self.token = token
        self.number_type = number_type


class Evaluator:
    r"""
    求值器
    :param expression: 构建的表达式. 该参数应该和Parser阶段一致
    :param tokens: 构建的Token流. 该参数应该和Parser阶段一致
    :param ast: 构建的AST树
    """

    def __init__(self, expression: str, tokens: list[Token], ast: ASTTree):
        self.expression = expression
        self.tokens = tokens
        self.ast = ast
        self.result: list[list[Token]] = [self.tokens]
        self.time_cost = -1

    def evaluate(self):
        r"""
        执行求值
        :return: None
        """

    def execute(self):
        r"""
        执行求值器
        :return: None
        """
        start_time = time.time_ns()
        self.evaluate()
        self.time_cost = time.time_ns() - start_time

    r"""
    静态方法
    """

    # 四则运算
    @staticmethod
    def addition(augend: Number, addend: Number) -> list[Token]:
        r"""
        计算加法
        :param augend: 被加数
        :param addend: 加数
        :return: 加法运算的结果
        """

        # 有理数相加
        if augend.TYPE == addend.TYPE == Number.TYPE.RATIONAL:
            ...
        # 无理数相加
        elif augend.TYPE == addend.TYPE == Number.TYPE.IRRATIONAL:
            ...
        # 有理数加无理数
        else:
            ...

    @staticmethod
    def subtraction(minuend: Number, subtrahend: Number) -> list[Token]:
        r"""
        计算减法
        :param minuend: 被减数
        :param subtrahend: 减数
        :return: 加法运算的结果
        """

    @staticmethod
    def multiplication(factor_1: Number, factor_2: Number) -> list[Token]:
        r"""
        计算乘法
        :param factor_1: 因数1
        :param factor_2: 因数2
        :return: 乘法运算的结果
        """

    @staticmethod
    def division(dividend: Number, divisor: Number) -> list[Token]:
        r"""
        计算除法.结果化至最简形式
        :param dividend: 被除数
        :param divisor: 除数
        :return: 除法运算的结果
        """


class Function:
    r"""
    函数
    """

    """
    代数函数
    """

    class Pow:
        r"""
        指数函数
        """

        @staticmethod
        def pow(x: list[Token], y: list[Token]) -> list[Token]:
            r"""
            计算指数函数
            :param x: 底数Token流
            :param y: 次数Token流
            :return: 计算结果
            """

        @staticmethod
        def sqrt(x: list[Token]) -> list[Token]:
            r"""
            计算开根号函数
            :param x: 被开根号的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("1/2"))

        @staticmethod
        def sq(x: list[Token]) -> list[Token]:
            r"""
            计算二次方函数
            :param x: 被二次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("2"))

        @staticmethod
        def cub(x: list[Token]) -> list[Token]:
            r"""
            计算三次方函数
            :param x: 被三次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("3"))

        @staticmethod
        def rec(x: list[Token]) -> list[Token]:
            r"""
            计算倒数函数
            :param x: 被计算倒数的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("-1"))

    """
    超越函数
    """

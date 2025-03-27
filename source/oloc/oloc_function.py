r"""
:author: WaterRun
:date: 2025-03-27
:file: oloc_function.py
:description: Oloc function
"""
from oloc_token import Token
import oloc_lexer as lexer


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
            return Function.Pow.pow(x, lexer.Lexer.tokenizer("1/2"))

        @staticmethod
        def sq(x: list[Token]) -> list[Token]:
            r"""
            计算二次方函数
            :param x: 被二次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, lexer.Lexer.tokenizer("2"))

        @staticmethod
        def cub(x: list[Token]) -> list[Token]:
            r"""
            计算三次方函数
            :param x: 被三次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, lexer.Lexer.tokenizer("3"))

        @staticmethod
        def rec(x: list[Token]) -> list[Token]:
            r"""
            计算倒数函数
            :param x: 被计算倒数的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, lexer.Lexer.tokenizer("-1"))

    """
    超越函数
    """
r"""
:author: WaterRun
:date: 2025-03-27
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

from math import gcd
from oloc_token import Token
from oloc_exceptions import *


class Evaluator:
    r"""
    求值器
    """

    r"""
    静态方法
    """

    # 四则运算
    @staticmethod
    def addition(augend: list[Token, Token, Token], addend: list[Token, Token, Token]) -> list[Token]:
        r"""
        计算加法
        :param augend: 被加数
        :param addend: 加数
        :return: 加法运算的结果
        """

    @staticmethod
    def subtraction(minuend: list[Token, Token, Token], subtrahend: list[Token, Token, Token]) -> list[Token]:
        r"""
        计算减法
        :param minuend: 被减数
        :param subtrahend: 减数
        :return: 加法运算的结果
        """

    @staticmethod
    def multiplication(factor_1: list[Token, Token, Token], factor_2: list[Token, Token, Token]) -> list[Token]:
        r"""
        计算乘法
        :param factor_1: 因数1
        :param factor_2: 因数2
        :return: 乘法运算的结果
        """

    @staticmethod
    def division(dividend: list[Token, Token, Token], divisor: list[Token, Token, Token]) -> list[Token]:
        r"""
        计算除法
        :param dividend: 被除数
        :param divisor: 除数
        :return: 除法运算的结果
        """

    # 分数化简
    @staticmethod
    def simplify(fraction_tokens: list[Token, Token, Token]) -> list[Token] or list[Token, Token, Token]:
        r"""
        化简传入的分数Token流
        :param fraction_tokens: 传入的分数Token流, 依次是整数, 分数线, 整数
        :return: 化简后的分数Token流, 或整数Token流(如果可能)
        """
        numerator = int(fraction_tokens[0].value)  # 分子
        denominator = int(fraction_tokens[2].value)  # 分母

        # 计算分子和分母的最大公约数
        divisor = gcd(numerator, denominator)

        # 化简分子和分母
        simplified_numerator = numerator // divisor
        simplified_denominator = denominator // divisor

        # 如果能化简为整数
        if simplified_denominator == 1:
            # 返回单个整数Token
            return [
                Token(
                    Token.TYPE.INTEGER,
                    str(simplified_numerator),
                    [fraction_tokens[0].range[0], fraction_tokens[2].range[1]]  # 范围覆盖整个分数的原范围
                )
            ]

        # 返回化简后的分数Token流
        return [
            Token(
                Token.TYPE.INTEGER,
                str(simplified_numerator),
                [fraction_tokens[0].range[0], fraction_tokens[0].range[0] + len(str(simplified_numerator))]
            ),
            Token(
                Token.TYPE.OPERATOR,
                "/",
                [fraction_tokens[0].range[0] + len(str(simplified_numerator)),
                 fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1]
            ),
            Token(
                Token.TYPE.INTEGER,
                str(simplified_denominator),
                [fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1,
                 fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1 + len(str(simplified_denominator))]
            )
        ]


"""test"""
if __name__ == '__main__':
    print(Evaluator.simplify([Token(Token.TYPE.INTEGER, "20", [0, 2]),
                              Token(Token.TYPE.OPERATOR, "/", [2, 3]),
                              Token(Token.TYPE.INTEGER, "40", [3, 5])]))

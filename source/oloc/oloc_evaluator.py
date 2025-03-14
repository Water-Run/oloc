"""
:author: WaterRun
:date: 2025-03-14
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

from math import gcd
from oloc_token import Token
from oloc_exceptions import *


class Function:
    r"""
    函数
    """

    r"""
    代数函数
    """


class Evaluator:
    r"""
    求值器
    """

    r"""
    静态方法
    """

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

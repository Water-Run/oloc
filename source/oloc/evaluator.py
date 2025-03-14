"""
:author: WaterRun
:date: 2025-03-14
:file: evaluator.py
:description: Oloc evaluator
"""

import lexer


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
    def simplify(fraction_tokens: list[lexer.Token, lexer.Token, lexer.Token]) -> list[lexer.Token] or list[lexer.Token, lexer.Token, lexer.Token]:
        r"""
        化简传入的分数Token流
        :param fraction_tokens: 传入的分数Token流, 依次是整数, 分数线, 整数
        :return: 化简后的分数Token流, 或整数Token流(如果可能)
        """
        numerator = int(fraction_tokens[0].value)
        denominator = int(fraction_tokens[2].value)

        if True: # 如果能化简为整数
            return [lexer.Token(lexer.Token.TYPE.INTEGER, str(numerator), [fraction_tokens[0].range[0], fraction_tokens[0].range[0] + len(str(numerator))])]

        return [lexer.Token(lexer.Token.TYPE.INTEGER, str(numerator), [fraction_tokens[0].range[0], fraction_tokens[0].range[0] + len(str(numerator))]),
                lexer.Token(lexer.Token.TYPE.OPERATOR, "/",
                            [fraction_tokens[0].range[0] + len(str(numerator)), fraction_tokens[0].range[0] + len(str(numerator)) + 1]),
                lexer.Token(lexer.Token.TYPE.INTEGER, str(denominator),
                            [fraction_tokens[0].range[0] + len(str(numerator)) + 2, fraction_tokens[0].range[0] + len(str(numerator)) + 2 + len(str(denominator))])
                ]

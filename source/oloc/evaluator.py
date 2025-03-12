"""
:author: WaterRun
:date: 2025-03-12
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

    @staticmethod
    def abs(number: lexer.Token) -> lexer.Token:
        ...


class Evaluator:
    r"""
    求值器
    """

    r"""
    静态方法
    """

    @staticmethod
    def simplify(token_flow: list[lexer.Token]) -> [lexer.Token, lexer.Token]:
        r"""
        化简分数
        当分数可化简为整数时,返回整数结果
        :param token_flow: 待化简的分数流.其中,第一项必须是分子,最后一项必须是分母
        :return: 化简后结果Token流.第一项是分子,第二项是分母
        """
        ...

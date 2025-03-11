"""
:author: WaterRun
:date: 2025-03-11
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
    def simplify(numerator: lexer.Token, denominator: lexer.Token) -> [lexer.Token, lexer.Token]:
        r"""
        化简分数
        当分数可化简为整数时,返回整数结果
        :param numerator: 待化简的分数分子
        :param denominator: 待化简的分数分母
        :return: 化简后结果Token流.第一项是分子,第二项是分母
        """

        def _get_gcd(num1: int, num2: int) -> int:
            r"""
            计算两个整数的最大公约数（使用欧几里得算法）
            :param num1: 整数 1
            :param num2: 整数 2
            :return: 最大公约数
            """
            while num2 != 0:
                num1, num2 = num2, num1 % num2
            return abs(num1)  # 返回正数作为最大公约数

        numerator, denominator = map(int, (numerator, denominator))

        gcd_value = _get_gcd(numerator, denominator)

        numerator //= gcd_value
        denominator //= gcd_value

        return [lexer.Token(lexer.Token.TYPE.INTEGER, str(numerator), None), lexer.Token(lexer.Token.TYPE.INTEGER, str(denominator), None)]

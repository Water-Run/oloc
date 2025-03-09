"""
:author: WaterRun
:date: 2025-03-09
:file: lexer.py
:description: Oloc lexer
"""

from enum import Enum


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression

    class TYPE(Enum):
        r"""
        枚举表达式中的所有类型
        """
        # 算术运算符
        OPERATOR = 'operator'

        # 数字(分数视为整数相除)
        INT = 'integer'
        PERCENTAGE = 'percentage'
        MIX = 'mixed fraction'
        FINITE = 'finite decimal expansion'
        INFINITE = 'infinite recurring decimal'
        PRIME = 'prime irrational number'
        SHORT = 'Customizing short irrational numbers'
        LONG = 'Customizing long irrational numbers'

        # 分组运算符
        LBRACKET = 'left bracket'
        RBRACKET = 'right bracket'

        # 函数
        FUNC = 'function'
        PARAM = 'function parameter'
        separator = 'function parameter separator'

    r"""
    静态方法
    """

    @staticmethod
    def tokenizer(expression: str) -> list:
        ...

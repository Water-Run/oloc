r"""
:author: WaterRun
:date: 2025-04-06
:file: oloc_result.py
:description: Oloc result
"""

import time

from typing import Any
from fractions import Fraction

from oloc_token import Token
from oloc_exceptions import *
from oloc_preprocessor import Preprocessor
from oloc_lexer import Lexer
from oloc_parser import Parser
from oloc_evaluator import Evaluator

import oloc_utils as utils


def output_filter(tokens: list[Token]) -> str:
    r"""
    格式化过滤Token流并输出
    :param tokens: 待过滤输出的token流
    :return: 过滤后的生成的表达式字符串
    """

    def _add_separator(num: Token, separator: str, thresholds: int, interval: int) -> str:
        r"""
        添加数字分隔符
        :param num: 待添加的数字（Token 类型，需要有 num.value 属性）
        :param separator: 分隔符形式
        :param thresholds: 分隔符阈值（大于该值才添加分隔符）
        :param interval: 分隔符间隔（每隔 interval 个字符插入一个分隔符）
        :return: 添加分隔符后的字符串数字
        """
        # 如果数字长度小于等于阈值，直接返回原始值
        if len(num.value) <= thresholds:
            return num.value

        # 倒序插入分隔符（从右向左操作）
        reversed_num = num.value[::-1]  # 将字符串数字反转
        parts = [
            reversed_num[i:i + interval] for i in range(0, len(reversed_num), interval)
        ]  # 按间隔切分为块
        after_add = separator.join(parts)  # 使用分隔符连接
        return after_add[::-1]  # 再次反转回原始顺序

    configs = utils.get_formatting_output_function_options_table()

    between_token = " " * configs["readability"]["space between tokens"]
    number_seperator = "," if configs["custom"]["underline-style number separator"] else "_"

    ascii_native_irrational_map = {"π": "pi", "𝑒": "e"}
    superscript_map = {'1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '0': '⁰'}

    result = ""

    # 字符串处理
    for index, temp_token in enumerate(tokens):

        # 当不启用保留无理数参数时,舍弃无理数参数
        if temp_token.type == Token.TYPE.IRRATIONAL_PARAM and not configs["custom"]["retain irrational param"]:
            continue

        elif temp_token.type == Token.TYPE.NATIVE_IRRATIONAL and configs["custom"]["non-ascii character form native irrational"]:
            result += ascii_native_irrational_map[temp_token.value]

        elif temp_token.type == Token.TYPE.INTEGER:
            result += _add_separator(temp_token, number_seperator, configs["readability"]["number separators add thresholds"], configs["readability"]["number separator interval"])

        else:
            result += temp_token.value

        # 添加Token间隔空格
        if 1 < index < len(tokens) - 1:
            result += between_token

    return result


class OlocResult:
    r"""
    表达oloc计算结果的类，具有不可变性。
    一旦实例化,OlocResult 的属性无法修改或删除。

    :param expression: 要计算的原始表达式
    :param preprocessor: 构造结果的预处理器
    :param lexer: 构造结果的词法分析器
    :param parser: 构造结构的语法分析器
    :param evaluator: 构造结果的求值器
    """

    def __init__(self, expression: str, preprocessor: Preprocessor, lexer: Lexer, parser: Parser, evaluator: Evaluator):

        start = time.time_ns()

        self._expression = expression
        self._preprocessor = preprocessor
        self._lexer = lexer
        self._parser = parser
        self._evaluator = evaluator

        self._result: list[str] = []

        for tokens in self._evaluator.result:
            self._result.append(output_filter(tokens))

        self._time_cost = time.time_ns() - start

        self._detail: dict[any] = {
            "expression": {
                "input": self._expression,
                "preprocessor": self._preprocessor.expression,
                "lexer": self._lexer.expression,
                "parser": self._parser.expression,
                "evaluator": self._evaluator.expression,
            },
            "token flow": {
                "lexer": self._lexer.tokens,
                "parser": self._parser.tokens,
                "evaluator": self._evaluator.tokens,
            },
            "ast": {
                "parser": self._parser.ast,
                "evaluator": self._evaluator.ast,
            },
            "time cost": {
                "preprocessor": self._preprocessor.time_cost,
                "lexer": self._lexer.time_cost,
                "parser": self._parser.time_cost,
                "evaluator": self._evaluator.time_cost,
                "result": self._time_cost
            },
            "result": self._result,
        }

    @property
    def expression(self) -> str:
        r"""
        获取表达式字符串。
        :return: 表达式字符串
        """
        return self._expression

    @property
    def result(self) -> List[str]:
        r"""
        获取表达式计算结果的字符串列表。
        :return: 结果字符串列表
        """
        return self._result

    @property
    def time_cost(self) -> float:
        r"""
        获取总计算耗时
        :return: 计算耗时(ms)
        """
        return (self._time_cost + self._preprocessor.time_cost + self._lexer.time_cost + self._parser.time_cost + self._evaluator.time_cost) / 1000000

    @property
    def detail(self) -> dict:
        r"""
        获取计算细节
        :return: 计算细节字典
        """
        return self._detail

    def __str__(self) -> str:
        r"""
        将 OlocResult 转换为字符串，返回 result 列表的最后一项。
        :return: result 列表的最后一项。如果列表为空，返回空字符串
        """
        return self._result[-1] if self._result else ""

    def __repr__(self) -> str:
        r"""
        返回 OlocResult 对象的字符串表示形式。
        :return: 对象的字符串表示形式
        """
        return f"OlocResult(expression={self._expression!r}, result={self._result!r})"

    def __float__(self) -> float:
        r"""
        转换为浮点型。
        :raises OlocConversionError: 如果无法进行转换(如缺失无理数参数的无理数)
        :return: 转化后的浮点数
        """

    def __int__(self) -> int:
        r"""
        转换为整型。(先转化为浮点)
        :return: 转化后的整数
        """
        return int(self.__float__())

    def get_fraction(self) -> Fraction:
        r"""
        转化为Python原生的Fraction类型。(先转化为浮点)
        :return: Fraction类型的结果
        """

    def format_detail(self, simp: bool = True) -> str:
        r"""
        获取格式化计算细节
        :param simp: 是否返回简化模式结果
        :return: 格式化计算细节字符串
        """
        if simp:
            return f""
        else:
            return f""

    def __setattr__(self, name: str, value: Any) -> None:
        r"""
        禁止修改 OlocResult 的属性。
        :raises AttributeError: 如果尝试修改已存在的属性
        """
        if hasattr(self, name):
            raise AttributeError(f"OlocResult is immutable. Cannot modify attribute '{name}'.")
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        r"""
        禁止删除 OlocResult 的属性。
        :raises AttributeError: 如果尝试删除属性
        """
        raise AttributeError(f"OlocResult is immutable. Cannot delete attribute '{name}'.")


"""test"""
if __name__ == "__main__":
    ...

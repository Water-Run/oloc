r"""
:author: WaterRun
:date: 2025-03-24
:file: oloc_result.py
:description: Oloc result
"""
from typing import List, Any
from fractions import Fraction
from oloc_token import Token
import oloc_utils as utils


def output_filter(tokens: list[Token]) -> str:
    r"""
    格式化过滤Token流并输出
    :param tokens: 待过滤输出的token流
    :return: 过滤后的生成的表达式字符串
    """
    configs = utils.get_formatting_output_function_options_table()

    between_token = " " * configs["space between token"]
    number_seperator = "," if configs["underline-style number separator"] else "_"

    result = ""

    for temp_token in tokens:
        temp_value = temp_token.value

        # 当不启用保留无理数参数时,舍弃无理数参数
        if temp_token.type == Token.TYPE.IRRATIONAL_PARAM and not configs["retain irrational param"]:
            continue

        # 添加Token间隔空格
        if len(tokens) > 1:
            result += between_token

    return result


class OlocResult:
    r"""
    表达oloc计算结果的类，具有不可变性。
    一旦实例化,OlocResult 的属性无法修改或删除。

    :param expression: 要计算的原始表达式
    :param result: 表达式计算结果的字符串列表
    :raises TypeError: 如果输入的参数类型不正确
    """

    def __init__(self, expression: str, result: List[str]) -> None:
        if not isinstance(expression, str):
            raise TypeError("Expression must be a string.")
        if not isinstance(result, list) or not all(isinstance(s, str) for s in result):
            raise TypeError("Result must be a list of strings.")
        self._expression = expression
        self._result = result
        self._raw_result: str | None = None

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
        :raises OlocFloatationError: 如果无法进行转换(如缺失无理数参数的无理数)
        :return: 转化后的浮点数
        """

    def __int__(self) -> int:
        r"""
        转换为整型。(先转化为浮点)
        :return: 转化后的整数
        """

    def get_fraction(self) -> Fraction:
        r"""
        转化为Python原生的Fraction类型。(先转化为浮点)
        :return: Fraction类型的结果
        """

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

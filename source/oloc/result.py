r"""
:author: WaterRun
:date: 2025-03-06
:file: result.py
:description: Oloc result
"""
from typing import List, Dict, Any


class OlocResult:
    r"""
    表达oloc计算结果的类，具有不可变性。
    一旦实例化,OlocResult 的属性无法修改或删除。

    :param expression: 要计算的表达式
    :param result: 表达式计算结果的字符串列表
    :raises: TypeError: 如果输入的参数类型不正确
    """

    def __init__(self, expression: str, result: List[str]) -> None:
        if not isinstance(expression, str):
            raise TypeError("Expression must be a string.")
        if not isinstance(result, list) or not all(isinstance(s, str) for s in result):
            raise TypeError("Result must be a list of strings.")
        self._expression = expression
        self._result = result

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

    def __dict__(self) -> Dict[str, Any]:
        r"""
        将 OlocResult 转换为字典。

        :return: 表示 OlocResult 的字典
        """
        return {"expression": self._expression, "result": self._result}

    def __list__(self) -> List[str]:
        r"""
        将 OlocResult 转换为列表。

        :return: result 列表
        """
        return self._result

    def __float__(self) -> float:
        r"""
        转换为浮点型。

        :raises TypeError: 如果无法进行转换
        """
        raise TypeError("OlocResult does not support conversion to float.")

    def __int__(self) -> int:
        r"""
        转换为整型。

        :raises TypeError: 如果无法进行转换
        """
        raise TypeError("OlocResult does not support conversion to int.")

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
    
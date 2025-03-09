"""
:author: WaterRun
:date: 2025-03-09
:file: exceptions.py
:description: Oloc exceptions
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class OlocException(ABC, Exception):
    r"""
    所有 Oloc 异常的抽象基类。

    该类为异常消息提供了标准结构，
    要求子类定义一个异常类型枚举类。
    """

    @abstractmethod
    class ExceptionType(Enum):
        r"""
        异常类型的抽象内部类。

        子类必须定义此枚举类，以提供特定的消息
        和与其异常类型相关的上下文信息。
        """
        ...

    def __init__(self, exception_type: Enum, expression: str, positions: List[int]):
        r"""
        使用特定的异常类型、表达式和错误位置初始化异常。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        """
        self.exception_type = exception_type
        self.expression = expression
        self.positions = positions
        super().__init__(self.__str__())

    def __str__(self):
        r"""
        生成异常的详细字符串表示。

        :return: 描述错误的格式化字符串
        """
        marker_line = self._generate_marker_line()
        return (
            f"{self.exception_type.value[0].format(time_limit=getattr(self, 'time_limit', 0))}\n"
            f"{self.expression}\n"
            f"{marker_line}\n"
            f"Hint: {self.exception_type.value[1]}"
        )

    def _generate_marker_line(self) -> str:
        r"""
        根据指定位置生成带有 '^' 标记的定位行。

        :return: 一个字符串，包含标记错误位置的 '^'
        """
        marker_line = [' '] * len(self.expression)
        for pos in self.positions:
            if 0 <= pos < len(self.expression):
                marker_line[pos] = '^'
        return ''.join(marker_line)

    def __reduce__(self):
        r"""
        自定义序列化逻辑，用于支持 multiprocessing.Queue 的序列化。
        """
        return (
            self.__class__,  # 返回类本身
            (self.exception_type, self.expression, self.positions)  # 返回初始化所需的参数
        )


class OlocTimeOutException(OlocException):
    r"""
    当函数执行时间超出设定的最大时间时引发的异常
    """

    class ExceptionType(Enum):
        r"""
        定义 OlocTimeOutException 的异常类型的枚举类。
        """
        TIMEOUT = (
            "OlocTimeOutException: Calculation time exceeds the set maximum time of {time_limit:.1f}s",
            "Check your expression or modify time_limit to a larger value."
        )

    def __init__(self, exception_type: ExceptionType, expression: str, positions: List[int], time_limit: float,
                 elapsed_time: float):
        r"""
        初始化 OlocTimeOutException，包含时间限制和实际耗时。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param time_limit: 最大允许的执行时间
        :param elapsed_time: 实际花费的时间
        """
        self.time_limit = time_limit
        self.elapsed_time = elapsed_time
        super().__init__(exception_type, expression, positions)

    def __reduce__(self):
        r"""
        自定义序列化逻辑，用于支持 multiprocessing.Queue 的序列化。
        """
        return (
            self.__class__,
            (self.exception_type, self.expression, self.positions, self.time_limit, self.elapsed_time)
        )


class OlocCommentException(OlocException):
    r"""
    当注释的格式不匹配时引发的异常
    """

    class ExceptionType(Enum):
        r"""
        定义 OlocCommentException 的异常类型的枚举类。
        """
        MISMATCH_HASH = (
            "OlocCommentException: Mismatch '#' detected",
            "The content of free comments should be wrapped in a before and after '#'."
        )

    def __init__(self, exception_type: ExceptionType, expression: str, positions: List[int]):
        r"""
        初始化 OlocCommentException。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        """
        super().__init__(exception_type, expression, positions)


class OlocNumberSeparatorException(OlocException):
    r"""
    当数字分隔符规则被违反时引发的异常
    """

    class ExceptionType(Enum):
        r"""
        定义 OlocNumberSeparatorException 的异常类型的枚举类。
        """
        INVALID_SEPARATOR = (
            "OlocNumberSeparatorException: Invalid numeric separator detected",
            "Ensure commas are used correctly as numeric separators in rational numbers. Commas must not appear at "
            "the start, end, or consecutively."
        )

    def __init__(self, exception_type: ExceptionType, expression: str, positions: List[int]):
        r"""
        初始化 OlocNumberSeparatorException。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        """
        super().__init__(exception_type, expression, positions)


class OlocResultException(OlocException):
    r"""
    当结果中存在异常(即尝试读取OlocResult中的指定信息时)引发的异常
    """

    class ExceptionType(Enum):
        r"""
        定义 OlocResultException 的异常类型的枚举类。
        """
        NO_VALID_RESULT = (
            "OlocResultException: Calculations fail to yield valid results",
            "."
        )

        NON_CONVERTIBLE_RESULT = (
            "OlocResultException: Unable to convert `` in the result",
            ""
        )

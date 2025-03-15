"""
:author: WaterRun
:date: 2025-03-15
:file: oloc_exceptions.py
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
    class EXCEPTION_TYPE(Enum):
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
        生成异常的详细字符串表示，动态解析模板中的占位符。

        :return: 描述错误的格式化字符串
        """
        # 动态获取实例属性，填充模板中的占位符
        try:
            formatted_message = self.exception_type.value[0].format(**self.__dict__)
        except KeyError as e:
            raise KeyError(f"Missing required attribute for exception formatting: {e}")

        marker_line = self._generate_marker_line()
        return (
            f"{formatted_message}\n"
            f"{self.expression}\n"
            f"{marker_line}\n"
            f"Hint: {self.exception_type.value[1]}\n"
            f"--------------------------------------------------------------------------------------------\n"
            f"Try visit https://github.com/Water-Run/oloc for more information on oloc related tutorials :)"
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

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocTimeOutException 的异常类型的枚举类。
        """
        TIMEOUT = (
            "OlocTimeOutException: Calculation time exceeds the set maximum time of {time_limit:.1f}s",
            "Check your expression or modify time_limit to a larger value."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int], time_limit: float,
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

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocCommentException 的异常类型的枚举类。
        """
        MISMATCH_HASH = (
            "OlocCommentException: Mismatch '#' detected",
            "The content of free comments should be wrapped in a before and after '#'."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int]):
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

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocNumberSeparatorException 的异常类型的枚举类。
        """
        INVALID_SEPARATOR = (
            "OlocNumberSeparatorException: Invalid numeric separator detected",
            "Ensure commas are used correctly as numeric separators in rational numbers. Commas must not appear at "
            "the start, end, or consecutively."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int]):
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

    class EXCEPTION_TYPE(Enum):
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


class OlocInvalidTokenException(OlocException):
    r"""
    当Token不合法(即,Token的is_legal为False时)在静态检查流程中引发的异常
    """

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocInvalidTokenException 的异常类型的枚举类。
        """

        UNKNOWN_TOKEN = (
            "OlocInvalidTokenException: Token that Tokenizer could not parse `{token_content}`",
            "Check the documentation for instructions and check the expression."
        )

        INVALID_PERCENTAGE = (
            "OlocInvalidTokenException: Invalid percentage number `{token_content}`",
            "A percentage must consist of a whole number or a finite number of decimals followed by a `%`. e.g. 100%, "
            "0.125%"
        )

        INVALID_INFINITE_DECIMAL = (
            "OlocInvalidTokenException: Invalid infinite-decimal number `{token_content}`",
            "An infinite cyclic decimal must be followed by a finite cyclic decimal ending in 3-6 ` . ` or `:` "
            "followed by an integer. e.g. 1.23..., 2.34......, 10.1:2"
        )

        INVALID_FINITE_DECIMAL = (
            "OlocInvalidTokenException: Invalid finite-decimal number `{token_content}`",
            "A finite repeating decimal must consist of an integer with integer digits and a decimal point. e.g. "
            "3.14, 0.233"
        )

        INVALID_INTEGER = (
            "OlocInvalidTokenException: Invalid integer number `{token_content}`",
            "An integer must be composed of Arabic numerals from 0 to 9. e.g. 0, 1024, 54321"
        )

        INVALID_NATIVE_IRRATIONAL = (
            "OlocInvalidTokenException: Invalid native-irrational number `{token_content}`",
            "A primitive irrational number must be one of `π` or `𝑒`."
        )

        INVALID_SHORT_CUSTOM_IRRATIONAL = (
            "OlocInvalidTokenException: Invalid short-custom-irrational number `{token_content}`",
            "A short custom irrational number must be a non-operator and non-digit character, including an optional "
            "`?` expression. The character between the end and `?` can only be a positive or negative sign or an "
            "integer or a finite decimal (with a sign). e.g. x, y-?, i3.14?, s+2?"
        )

        INVALID_LONG_CUSTOM_IRRATIONAL = (
            "OlocInvalidTokenException: Invalid long-custom-irrational number `{token_content}`",
            "A long custom irrational number must be wrapped in `<>`, including an optional `?` expression. The "
            "character between the end and `?` can only be a positive or negative sign or an integer or a finite "
            "decimal (with a sign). e.g. <ir>, <无理数>+?, <A long one>-3?, <irrational>0.12?"
        )

        INVALID_OPERATOR = (
            "OlocInvalidTokenException: Invalid operator `{token_content}`",
            "Check the expression, or check the tutorial (and symbol-mapping-table)."
        )

        INVALID_BRACKET = (
            "OlocInvalidTokenException: Invalid bracket `{token_content}`",
            "The brackets can only be one of `()`, `[]`, `{}`. Check the expression, or refer to the tutorial for "
            "information about grouping operators."
        )

        INVALID_FUNCTION = (
            "OlocInvalidTokenException: Invalid function `{token_content}`",
            "Check out the tutorial or the function-conversion-table for more information."
        )

        INVALID_PARAM_SEPARTOR = (
            "OlocInvalidTokenException: Invalid param-separator `{token_content}`",
            "The function parameter separator can only be `,` or `;`. If your parameters contain numeric separators, "
            "the parameter separator can only be ';'."
        )

        INVALID_IRRATIONAL_PARAM = (
            "OlocInvalidTokenException: Invalid irrational param `{token_content}`",
            "An irrational number parameter expression can only be an integer or a signed or unsigned integer or "
            "decimal with a plus or minus sign. (Native irrational numbers only parse the integer part)."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int], token_content: str):
        r"""
        初始化 OlocInvalidTokenException，包含异常类型和 Token 内容。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param token_content: 引发异常的 Token 内容
        """
        self.token_content = token_content

        main_message = exception_type.value[0].format(token_content=token_content)
        suggestion = exception_type.value[1]

        self.message = f"{main_message} {suggestion}"

        # 调用父类初始化
        super().__init__(exception_type, expression, positions)


class OlocInvalidCalculationException(OlocException):
    r"""
    当出现不合法的计算时抛出此异常
    """

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocInvalidTokenException 的异常类型的枚举类。
        """

        DIVIDE_BY_ZERO = (
            "OlocInvalidCalculationException: Divide-by-zero detected in the computational expression `{"
            "computing_unit}`",
            "The divisor or denominator may not be zero. Check the expression."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int], computing_unit: str):
        r"""
        初始化 OlocInvalidCalculationException，包含异常类型和 Token 内容。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param computing_unit: 引发异常的计算单元内容
        """
        self.computing_unit = computing_unit

        main_message = exception_type.value[0].format(computing_unit=computing_unit)
        suggestion = exception_type.value[1]

        self.message = f"{main_message} {suggestion}"

        # 调用父类初始化
        super().__init__(exception_type, expression, positions)


class OlocIrrationalNumberException(OlocException):
    r"""
    当存在无理数相关问题时引发的异常
    """

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocIrrationalNumberException 的异常类型的枚举类。
        """
        MISMATCH_LONG_LEFT_SIGN = (
            "OlocIrrationalNumberException: Mismatch '<' detected",
            "When declaring a custom long irrational number, `<` must match `>`. Check your expressions."
        )

        MISMATCH_LONG_RIGHT_SIGN = (
            "OlocIrrationalNumberException: Mismatch '>' detected",
            "When declaring a custom long irrational number, `>` must match `<`. Check your expressions."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int]):
        r"""
        初始化 OlocIrrationalNumberException。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        """
        super().__init__(exception_type, expression, positions)


class OlocInvalidBracketException(OlocException):
    r"""
    当存在括号相关问题时引发的异常
    """

    class EXCEPTION_TYPE(Enum):
        r"""
        定义 OlocInvalidBracketException 的异常类型的枚举类。
        """
        MISMATCH_LEFT_BRACKET = (
            "OlocInvalidBracketException: Mismatch `{err_bracket}` detected",
            "The left bracket must be matched by an identical right bracket. Check your expressions."
        )

        MISMATCH_RIGHT_BRACKET = (
            "OlocInvalidBracketException: Mismatch `{err_bracket}` detected",
            "The right bracket must be matched by an identical left bracket. Check your expressions."
        )

        INCORRECT_BRACKET_HIERARCHY = (
            "OlocInvalidBracketException: Bracket `{err_bracket}` hierarchy error",
            "Parentheses must follow the hierarchy: `()` `[]` `{}` in descending order."
        )

    def __init__(self, exception_type: EXCEPTION_TYPE, expression: str, positions: List[int], err_bracket: str):
        r"""
        初始化 OlocInvalidCalculationException，包含异常类型和 Token 内容。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param computing_unit: 引发异常的计算单元内容
        """
        self.err_bracket = err_bracket

        main_message = exception_type.value[0].format(err_bracket=err_bracket)
        suggestion = exception_type.value[1]

        self.message = f"{main_message} {suggestion}"

        # 调用父类初始化
        super().__init__(exception_type, expression, positions)
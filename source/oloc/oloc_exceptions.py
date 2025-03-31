r"""
:author: WaterRun
:date: 2025-03-31
:file: oloc_exceptions.py
:description: Oloc exceptions
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List


r"""
:author: WaterRun
:date: 2025-03-31
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
    class TYPE(Enum):
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
        # 默认异常名称，由子类覆盖
        if not hasattr(self, 'exception_name'):
            self.exception_name = self.__class__.__name__
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
            f"{self.exception_name}: {formatted_message}\n"
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

class OlocTimeOutError(OlocException):
    r"""
    当函数执行时间超出设定的最大时间时引发的异常
    """

    class TYPE(Enum):
        r"""
        定义 OlocTimeOutError 的异常类型的枚举类。
        """
        TIMEOUT = (
            "OlocTimeOutError: Calculation time exceeds the set maximum time of {time_limit:.1f}s",
            "Check your expression or modify time_limit to a larger value."
        )

    def __init__(self, exception_type: TYPE, expression: str, positions: List[int], time_limit: float,
                 elapsed_time: float):
        r"""
        初始化 OlocTimeOutError，包含时间限制和实际耗时。

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


class OlocSyntaxError(OlocException):
    r"""
    当出现语法错误时抛出此异常
    """

    class TYPE(Enum):
        r"""
        定义 OlocSyntaxError 的异常类型的枚举类。
        """
        # 注释相关异常
        COMMENT_MISMATCH = (
            "Mismatch '#' detected",
            "The content of free comments should be wrapped in a before and after '#'."
        )

        # 无理数格式相关异常
        IRRATIONAL_LEFT_BRACKET_MISMATCH = (
            "Mismatch '<' detected",
            "When declaring a custom long irrational number, `<` must match `>`. Check your expressions."
        )
        IRRATIONAL_RIGHT_BRACKET_MISMATCH = (
            "Mismatch '>' detected",
            "When declaring a custom long irrational number, `>` must match `<`. Check your expressions."
        )

        # 括号相关异常
        LEFT_BRACKET_MISMATCH = (
            "Mismatch `{primary_info}` detected",
            "The left bracket must be matched by an identical right bracket. Check your expressions."
        )
        RIGHT_BRACKET_MISMATCH = (
            "Mismatch `{primary_info}` detected",
            "The right bracket must be matched by an identical left bracket. Check your expressions."
        )
        BRACKET_HIERARCHY_ERROR = (
            "Bracket `{primary_info}` hierarchy error",
            "Parentheses must follow the hierarchy: `{}` `[]` `()` in descending order."
        )

        # 等号位置异常
        EQUAL_SIGN_MISPLACEMENT = (
            "Misplaced '=' detected",
            "The `=` can only appear in the last part of a valid expression."
        )

        # 函数参数异常
        FUNCTION_SEPARATOR_OUTSIDE = (
            "Function separator `{primary_info}` detected outside of function ({secondary_info})",
            "The function separator must be inside the function. If you expect the separator to be inside a function, "
            "check that the function name is valid."
        )
        POWER_FUNCTION_PARAM_ERROR = (
            "The parameter `{primary_info}` in the pow() is incorrect ({secondary_info})",
            "Check the documentation for the parameter description of pow()."
        )

        # 数字分隔符异常
        NUMERIC_SEPARATOR_ERROR = (
            "Invalid numeric separator detected",
            "Ensure commas are used correctly as numeric separators in rational numbers. If you expect `,` to be a "
            "function parameter, check that the function name is a legal function name in oloc. Commas must not "
            "appear at the start, end, or consecutively. When using numeric separators in a function, only `;` can be used to "
            "separate the arguments of the function."
        )

        # 保留字冲突异常
        RESERVED_WORD_CONFLICT = (
            "The name `{primary_info}` is a reserved word",
            "In oloc, reserved words begin with `__reserved`. You cannot use a name that conflicts with it."
        )

        # 静态检查异常
        DOT_SYNTAX_ERROR = (
            "Dot symbols detected during the static checking phase `{primary_info}`",
            "It's likely that there are illegal decimals. Decimals must have one and only one decimal point, "
            "distinguishing between preceding integer and decimal places. Checking the expression or submitting an "
            "issue."
        )
        COLON_SYNTAX_ERROR = (
            "Colon symbols detected during the static checking phase `{primary_info}`",
            "This can be caused by incorrectly displaying the infinite loop decimal statement. "
            "Checking the expression or submitting an issue."
        )
        UNEXPECTED_OPERATOR = (
            "Operator that should not be present during the static checking phase `{primary_info}`",
            "This operator should not be present during static processing. Checking the expression or submitting an "
            "issue."
        )
        OPERATOR_MISPLACEMENT = (
            "Misplaced operator `{primary_info}`",
            "Syntactic qualifications for unary and binary operators, in particular. Check the documentation for "
            "information. Checking the expression or submitting an issue."
        )
        INVALID_FUNCTION_NAME = (
            "Function names that should not appear in the static checking phase `{primary_info}`",
            "This function should not be present during static processing. Checking the expression or submitting an "
            "issue."
        )
        FUNCTION_MISPLACEMENT = (
            "Misplaced function call `{primary_info}`",
            "Function declarations must be followed by a left bracket. If the function is not the first element, "
            "it may be preceded by left brackets or an operator. Checking the expression or submitting an issue."
        )
        UNEXPECTED_BRACKET = (
            "Bracket that should not be present during the static checking phase `{primary_info}`",
            "This bracket should not be present during static processing. Checking the expression or submitting an "
            "issue."
        )
        IRRATIONAL_PARAM_ERROR = (
            "Irrational number of parameters `{primary_info}` for which static checking fails",
            "This may be due to the fact that the previous Token of the irrational number parameter is not legal. An "
            "irrational number argument can only come after an irrational number or a result (such as a function) "
            "that may be irrational. Check the expression to ensure that the structure of the irrational number "
            "argument is legal."
        )
        FUNCTION_PARAM_SEPARATOR_ERROR = (
            "Invalid function parameter separator detected `{primary_info}`",
            "A legal function argument separator can only be preceded by a number or a right bracket. "
            "If the latter item begins with an operator, it must be in the form of a legal unary operator. "
            "Checking the expression or submitting an issue."
        )
        UNEXPECTED_TOKEN_TYPE = (
            "Token types that should not be present `{primary_info}`",
            "Token of this type should not be retained during the static checking phase. Checking the expression or "
            "submitting an issue."
        )
        ABSOLUTE_SYMBOL_MISMATCH = (
            "Mismatched absolute symbol `{primary_info}`",
            "Absolute value symbols must be paired left and right. Checking the expression or "
            "submitting an issue."
        )

    def __init__(self, exception_type: TYPE, expression: str, positions: List[int],
                 primary_info: str = None, secondary_info: str = None):
        r"""
        初始化 OlocSyntaxError，包含异常类型和相关信息。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param primary_info: 主要异常信息，例如错误的符号、标记等
        :param secondary_info: 辅助异常信息，提供额外的上下文
        """
        self.exception_name = "OlocSyntaxError"
        self.primary_info = primary_info
        self.secondary_info = secondary_info

        super().__init__(exception_type, expression, positions)

    def __reduce__(self):
        r"""
        自定义序列化逻辑，用于支持 multiprocessing.Queue 的序列化。
        """
        return (
            self.__class__,
            (self.exception_type, self.expression, self.positions, self.primary_info, self.secondary_info)
        )


class OlocCalculationError(OlocException):
    r"""
    当出现计算错误时抛出此异常
    """

    class TYPE(Enum):
        r"""
        定义 OlocCalculationError 的异常类型的枚举类。
        """
        DIVIDE_BY_ZERO = (
            "Divide-by-zero detected in the computational expression `{primary_info}`",
            "The divisor or denominator may not be zero. Check the expression."
        )

    def __init__(self, exception_type: TYPE, expression: str, positions: List[int],
                 primary_info: str = None, secondary_info: str = None):
        r"""
        初始化 OlocCalculationError，包含异常类型和计算单元内容。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param primary_info: 主要异常信息，例如引发异常的计算单元
        :param secondary_info: 辅助异常信息，提供额外的上下文
        """
        self.exception_name = "OlocCalculationError"
        self.primary_info = primary_info
        self.secondary_info = secondary_info

        super().__init__(exception_type, expression, positions)

    def __reduce__(self):
        r"""
        自定义序列化逻辑，用于支持 multiprocessing.Queue 的序列化。
        """
        return (
            self.__class__,
            (self.exception_type, self.expression, self.positions, self.primary_info, self.secondary_info)
        )


class OlocValueError(OlocException):
    r"""
    当出现无效值或格式错误时抛出此异常
    """

    class TYPE(Enum):
        r"""
        定义 OlocValueError 的异常类型的枚举类。
        """
        # Token错误
        UNKNOWN_TOKEN = (
            "Token that Tokenizer could not parse `{primary_info}`",
            "Check the documentation for instructions and check the expression."
        )
        INVALID_PERCENTAGE = (
            "Invalid percentage number `{primary_info}`",
            "A percentage must consist of a whole number or a finite number of decimals followed by a `%`. e.g. 100%, "
            "0.125%"
        )
        INVALID_INFINITE_DECIMAL = (
            "Invalid infinite-decimal number `{primary_info}`",
            "An infinite cyclic decimal must be followed by a finite cyclic decimal ending in 3-6 ` . ` or `:` "
            "followed by an integer. e.g. 1.23..., 2.34......, 10.1:2. The declaration `:` cannot be used when the "
            "first decimal place is a round-robin place."
        )
        INVALID_FINITE_DECIMAL = (
            "Invalid finite-decimal number `{primary_info}`",
            "A finite repeating decimal must consist of an integer with integer digits and a decimal point. e.g. "
            "3.14, 0.233"
        )
        INVALID_INTEGER = (
            "Invalid integer number `{primary_info}`",
            "An integer must be composed of Arabic numerals from 0 to 9. e.g. 0, 1024, 54321"
        )
        INVALID_NATIVE_IRRATIONAL = (
            "Invalid native-irrational number `{primary_info}`",
            "A primitive irrational number must be one of `π` or `𝑒`."
        )
        INVALID_SHORT_CUSTOM_IRRATIONAL = (
            "Invalid short-custom-irrational number `{primary_info}`",
            "A short custom irrational number must be a non-operator and non-digit character, including an optional "
            "`?` expression. The character between the end and `?` can only be a positive or negative sign or an "
            "integer or a finite decimal (with a sign). e.g. x, y-?, i3.14?, s+2?"
        )
        INVALID_LONG_CUSTOM_IRRATIONAL = (
            "Invalid long-custom-irrational number `{primary_info}`",
            "A long custom irrational number must be wrapped in `<>`, including an optional `?` expression. The "
            "character between the end and `?` can only be a positive or negative sign or an integer or a finite "
            "decimal (with a sign). e.g. <ir>, <无理数>+?, <A long one>-3?, <irrational>0.12?"
        )
        INVALID_OPERATOR = (
            "Invalid operator `{primary_info}`",
            "Check the expression, or check the tutorial (and symbol-mapping-table)."
        )
        INVALID_BRACKET = (
            "Invalid bracket `{primary_info}`",
            "The brackets can only be one of `()`, `[]`, `{}`. Check the expression, or refer to the tutorial for "
            "information about grouping operators."
        )
        INVALID_FUNCTION = (
            "Invalid function `{primary_info}`",
            "This may be caused by splicing several consecutive legal function names. Check out the tutorial or the "
            "function-conversion-table for more information."
        )
        INVALID_PARAM_SEPARATOR = (
            "Invalid param-separator `{primary_info}`",
            "The function parameter separator can only be `,` or `;`. If your parameters contain numeric separators, "
            "the parameter separator can only be ';'."
        )
        INVALID_IRRATIONAL_PARAM = (
            "Invalid irrational param `{primary_info}`",
            "An irrational number parameter expression can only be an integer or a signed or unsigned integer or "
            "decimal with a plus or minus sign. (Native irrational numbers only parse the integer part)."
        )

    def __init__(self, exception_type: TYPE, expression: str, positions: List[int],
                 primary_info: str = None, secondary_info: str = None):
        r"""
        初始化 OlocValueError，包含异常类型和主要信息。

        :param exception_type: 异常的类型 (Enum)
        :param expression: 触发异常的原始表达式
        :param positions: 表示问题位置的列表
        :param primary_info: 主要异常信息，例如引发异常的Token内容
        :param secondary_info: 辅助异常信息，提供额外的上下文
        """
        self.exception_name = "OlocValueError"
        self.primary_info = primary_info
        self.secondary_info = secondary_info

        super().__init__(exception_type, expression, positions)

    def __reduce__(self):
        r"""
        自定义序列化逻辑，用于支持 multiprocessing.Queue 的序列化。
        """
        return (
            self.__class__,
            (self.exception_type, self.expression, self.positions, self.primary_info, self.secondary_info)
        )

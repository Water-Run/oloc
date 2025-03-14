r"""
:author: WaterRun
:date: 2025-03-14
:file: oloc_token.py
:description: oloc token
"""

import oloc_utils as utils
from oloc_exceptions import *


class Token:
    r"""
    表达式中的词元
    :param token_type: 词元的类别
    :param token_range: 词元在表达式中的范围(位置)
    :param token_value: 词元的实际值
    """

    class TYPE(Enum):
        r"""
        枚举词原的所有类型
        """
        # 数字类型
        PERCENTAGE = 'percentage'  # 百分数: 100%
        INFINITE_DECIMAL = 'infinite recurring decimal'  # 无限小数: 3.3... 或 2.3:4
        FINITE_DECIMAL = 'finite decimal'  # 有限小数: 3.14
        INTEGER = 'integer'  # 整数: 42

        # 无理数类型
        NATIVE_IRRATIONAL = 'native irrational number'  # 原生无理数: π, e
        SHORT_CUSTOM = 'short custom irrational'  # 短自定义无理数: x, y
        LONG_CUSTOM = 'long custom irrational'  # 长自定义无理数: <name>

        # 无理数参数类型
        IRRATIONAL_PARAM = 'irrational param'

        # 运算符
        OPERATOR = 'operator'  # 运算符: +, -, *, /等
        LBRACKET = 'left bracket'  # 左括号: (, [, {
        RBRACKET = 'right bracket'  # 右括号: ), ], }

        # 函数相关
        FUNCTION = 'function'  # 函数: sin, pow等
        PARAM_SEPARATOR = 'parameter separator'  # 参数分隔符: ,或;

        # 未知类型
        UNKNOWN = 'unknown'  # 无法识别的字符

    def __init__(self, token_type: TYPE, token_value: str = "", token_range: list[int, int] = None):
        if token_range is None:
            token_range = [0, 0]
        self.value = token_value
        if self.value == "":
            self.type = Token.TYPE.UNKNOWN
        self.type = token_type
        self.range = token_range
        self.is_legal = False
        self._check_legal()

    def __repr__(self):
        return f"Token({self.type.value}, '{self.value}, {self.range}')"

    def get_exception_type(self) -> OlocInvalidTokenException.EXCEPTION_TYPE:
        r"""
        返回对应的OlocInvalidTokenException.ExceptionType类型
        :return:
        """
        mapping = {
            Token.TYPE.PERCENTAGE: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_PERCENTAGE,
            Token.TYPE.INFINITE_DECIMAL: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_INFINITE_DECIMAL,
            Token.TYPE.FINITE_DECIMAL: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_FINITE_DECIMAL,
            Token.TYPE.INTEGER: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_SHORT_CUSTOM_IRRATIONAL,
            Token.TYPE.LONG_CUSTOM: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_LONG_CUSTOM_IRRATIONAL,
            Token.TYPE.OPERATOR: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_OPERATOR,
            Token.TYPE.LBRACKET: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_BRACKET,
            Token.TYPE.RBRACKET: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_BRACKET,
            Token.TYPE.FUNCTION: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_FUNCTION,
            Token.TYPE.PARAM_SEPARATOR: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_PARAM_SEPARTOR,
            Token.TYPE.IRRATIONAL_PARAM: OlocInvalidTokenException.EXCEPTION_TYPE.INVALID_IRRATIONAL_PARAM,
            Token.TYPE.UNKNOWN: OlocInvalidTokenException.EXCEPTION_TYPE.UNKNOWN_TOKEN,
        }
        return mapping[self.type]

    def _check_legal(self) -> bool:
        r"""
        检查自身的合法性
        :return: 自身是否是一个合法的Token
        """
        # 根据Token类型调用相应的检查方法
        checker_method_name = f"_check_{self.type.name.lower()}"
        if hasattr(self, checker_method_name):
            checker_method = getattr(self, checker_method_name)
            self.is_legal = checker_method()
        else:
            self.is_legal = False
        return self.is_legal

    def _check_integer(self) -> bool:
        r"""
        检查整数类型的Token的合法性
        :return: 是否合法
        """
        return self.value.isdigit()

    def _check_finite_decimal(self) -> bool:
        r"""
        检查有限小数类型的Token的合法性
        :return: 是否合法
        """
        if '.' in self.value:
            parts = self.value.split('.')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return True
        return False

    def _check_infinite_decimal(self) -> bool:
        r"""
        检查无限小数类型的Token的合法性
        :return: 是否合法
        """
        # 情况1: 以3-6个点结尾，如 3.14...
        if '.' in self.value and self.value.endswith(('...', '....', '.....', '......')):
            base = self.value.rstrip('.')
            if '.' in base:
                parts = base.split('.')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return True

        # 情况2: 以:加整数结尾，如 2.3:4
        if ':' in self.value:
            parts = self.value.split(':')
            if len(parts) == 2:
                decimal_part, integer_part = parts
                if '.' in decimal_part:
                    decimal_parts = decimal_part.split('.')
                    if len(decimal_parts) == 2 and decimal_parts[0].isdigit() and decimal_parts[1].isdigit():
                        if integer_part.isdigit():
                            return True

        return False

    def _check_percentage(self) -> bool:
        r"""
        检查百分数类型的Token的合法性
        :return: 是否合法
        """
        if self.value.endswith('%'):
            number_part = self.value[:-1]
            if '.' in number_part:
                parts = number_part.split('.')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return True
            elif number_part.isdigit():
                return True
        return False

    def _check_native_irrational(self) -> bool:
        r"""
        检查原生无理数类型的Token的合法性
        :return: 是否合法
        """
        if self.value in {'π', '𝑒'}:
            return True
        return False

    def _check_short_custom(self) -> bool:
        r"""
        检查自定义短无理数类型的Token的合法性
        :return: 是否合法
        """
        if self.value in set(utils.get_symbol_mapping_table().keys()):
            return False
        return True

    def _check_long_custom(self) -> bool:
        r"""
        检查自定义长无理数类型的Token的合法性
        :return: 是否合法
        """
        if not self.value.startswith("<") and self.value.endswith(">"):
            return False
        return True

    def _check_operator(self) -> bool:
        r"""
        检查运算符类型的Token的合法性
        :return: 是否合法
        """

        symbol_mapping_table = utils.get_symbol_mapping_table()
        # 排除分组运算符
        brackets = ['(', ')', '[', ']', '{', '}']

        # 检查是否在符号映射表中且不是括号
        return self.value in symbol_mapping_table.keys() and self.value not in brackets

    def _check_lbracket(self) -> bool:
        r"""
        检查左括号类型的Token的合法性
        :return: 是否合法
        """
        return self.value in ['(', '[', '{']

    def _check_rbracket(self) -> bool:
        r"""
        检查右括号类型的Token的合法性
        :return: 是否合法
        """
        return self.value in [')', ']', '}']

    def _check_param_separator(self) -> bool:
        r"""
        检查参数分隔符类型的Token的合法性
        :return: 是否合法
        """
        return self.value in [',', ';']

    def _check_function(self) -> bool:
        r"""
        检查函数类型的Token的合法性
        :return: 是否合法
        """

        function_list = utils.get_function_name_list()
        return self.value in function_list

    def _check_irrational_param(self) -> bool:
        r"""
        检查无理数参数类型的Token的合法性
        :return: 是否合法
        """
        if len(self.value) <= 1:
            return False

        # 检查值是否以 "?" 结尾
        if not self.value.endswith("?"):
            return False

        # 初始化小数点标志
        find_decimal_point = False
        # 检查首字符是否为 "+" 或 "-"
        start_index = 1 if self.value[0] in "+-" else 0

        # 遍历字符串中的每个字符（跳过首字符如果是符号）
        for c in self.value[start_index:-1]:
            if c == '.':
                # 如果已经找到一个小数点，则返回 False
                if find_decimal_point:
                    return False
                # 标记找到小数点
                find_decimal_point = True
            elif not c.isdigit():
                # 如果字符不是数字，则返回 False
                return False

        return True
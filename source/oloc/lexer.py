r"""
:author: WaterRun
:date: 2025-03-11
:file: lexer.py
:description: Oloc lexer
"""

import utils

import re
from exceptions import *


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
        MIXED_FRACTION = 'mixed fraction'  # 带分数: 3\1/2
        INFINITE_DECIMAL = 'infinite recurring decimal'  # 无限小数: 3.3... 或 2.3:4
        FINITE_DECIMAL = 'finite decimal'  # 有限小数: 3.14
        INTEGER = 'integer'  # 整数: 42
        FRACTION = 'fraction'  # 分数: 1/2

        # 无理数类型
        NATIVE_IRRATIONAL = 'native irrational number'  # 原生无理数: π, e
        SHORT_CUSTOM = 'short custom irrational'  # 短自定义无理数: x, y
        LONG_CUSTOM = 'long custom irrational'  # 长自定义无理数: <name>

        # 运算符
        OPERATOR = 'operator'  # 运算符: +, -, *, /等
        LBRACKET = 'left bracket'  # 左括号: (, [, {
        RBRACKET = 'right bracket'  # 右括号: ), ], }

        # 函数相关
        FUNCTION = 'function'  # 函数: sin, pow等
        PARAM_SEPARATOR = 'parameter separator'  # 参数分隔符: ,或;

        # 未知类型
        UNKNOWN = 'unknown'  # 无法识别的字符

    def __init__(self, token_type: TYPE, token_range: list[int, int], token_value: str = None):
        self.type = token_type
        self.range = token_range
        self.value = token_value if token_value is not None else None
        self.is_legal = False
        self._check_legal()

    def __repr__(self):
        return f"Token({self.type.value}, {self.range}, '{self.value}')"

    def _check_legal(self) -> bool:
        r"""
        检查自身的合法性
        :return: 自身是否是一个合法的Token
        """
        # 根据Token类型调用相应的检查方法
        checker_method_name = f"_check_{self.type.name.lower()}"
        if hasattr(self, checker_method_name) and self.value is not None:
            checker_method = getattr(self, checker_method_name)
            self.is_legal = checker_method()
        else:
            self.is_legal = False
        return self.is_legal

    # 各种检查方法定义，现在它们是实例方法而不是类方法
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
        return bool(re.match(r'^\d+\.\d+$', self.value))

    def _check_infinite_decimal(self) -> bool:
        r"""
        检查无限小数类型的Token的合法性
        :return: 是否合法
        """
        # 情况1: 以3-6个点结尾，如 3.14...
        if re.search(r'\.\d+\.{3,6}$', self.value):
            base = re.sub(r'\.{3,6}$', '', self.value)
            return bool(re.match(r'^\d+\.\d+$', base))

        # 情况2: 以:加整数结尾，如 2.3:4
        if ':' in self.value:
            match = re.match(r'^(\d+\.\d+):(\d+)$', self.value)
            return bool(match)

        return False

    def _check_fraction(self) -> bool:
        r"""
        检查分数类型的Token的合法性
        :return: 是否合法
        """
        return bool(re.match(r'^\d+/\d+$', self.value))

    def _check_mixed_fraction(self) -> bool:
        r"""
        检查带分数类型的Token的合法性
        :return: 是否合法
        """
        return bool(re.match(r'^\d+\\\d+/\d+$', self.value))

    def _check_percentage(self) -> bool:
        r"""
        检查百分数类型的Token的合法性
        :return: 是否合法
        """
        return bool(re.match(r'^\d+(\.\d+)?%$', self.value))

    def _check_native_irrational(self) -> bool:
        r"""
        检查原生无理数类型的Token的合法性
        :return: 是否合法
        """
        return bool(re.match(r'^[πe𝑒](\d+\?)?$', self.value))

    def _check_short_custom(self) -> bool:
        r"""
        检查自定义短无理数类型的Token的合法性
        :return: 是否合法
        """
        try:
            from utils import get_symbol_mapping_table

            symbol_mapping_table = get_symbol_mapping_table()

            # 检查第一个字符是否是自定义短无理数（不在映射表的键中）
            if len(self.value) < 1 or self.value[0] in symbol_mapping_table.keys():
                return False

            # 如果只有一个字符，是合法的
            if len(self.value) == 1:
                return True

            # 检查结尾是否有?
            if self.value.endswith('?'):
                # 去掉第一个字符和?后检查剩余部分
                remaining = self.value[1:-1]

                # 使用正则表达式检查剩余部分
                return bool(re.match(r'^[+-]$|^[+-]?\d+(\.\d+)?$', remaining))

            # 否则不合法
            return False
        except ImportError:
            # 处理utils模块导入失败的情况
            return False

    def _check_long_custom(self) -> bool:
        r"""
        检查自定义长无理数类型的Token的合法性
        :return: 是否合法
        """
        # 使用正则表达式检查长自定义无理数格式
        base_match = re.match(r'^<([^<>]+)>([+-]|\d+(\.\d+)?|[+-]\d+(\.\d+)?)?\?$', self.value)
        if base_match:
            return True

        # 简单格式 <name>
        return bool(re.match(r'^<[^<>]+>$', self.value))

    def _check_operator(self) -> bool:
        r"""
        检查运算符类型的Token的合法性
        :return: 是否合法
        """
        try:
            from utils import get_symbol_mapping_table

            symbol_mapping_table = get_symbol_mapping_table()
            # 排除分组运算符
            brackets = ['(', ')', '[', ']', '{', '}']

            # 检查是否在符号映射表中且不是括号
            return self.value in symbol_mapping_table.keys() and self.value not in brackets
        except ImportError:
            # 处理utils模块导入失败的情况
            return False

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
        try:
            from utils import get_function_name_list

            function_list = get_function_name_list()
            return self.value in function_list
        except ImportError:
            # 处理utils模块导入失败的情况
            return False


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression

    def execute(self):
        ...

    @staticmethod
    def _is_native_irrational(to_check: str) -> bool:
        r"""
        判断是否为原生无理数
        :param to_check: 待检查的字符
        :return: 如果是原生无理数(π或e)则返回True，否则返回False
        """
        return to_check in ["π", "𝑒"]

    @staticmethod
    def _is_operator(to_check: str) -> bool:
        r"""
        判断是否为运算符
        :param to_check: 待检查的字符
        :return: 如果是运算符则返回True，否则返回False
        """
        operators = list(utils.get_symbol_mapping_table().keys())
        operators = [op for op in operators if op and op not in "()[]{}<>"]  # 不包含分组运算符
        return to_check in operators

    @staticmethod
    def _is_bracket(to_check: str) -> bool:
        r"""
        判断是否为括号
        :param to_check: 待检查的字符
        :return: 如果是括号则返回True，否则返回False
        """
        return to_check in "()[]{}"

    @staticmethod
    def _is_separator(to_check: str) -> bool:
        r"""
        判断是否为函数参数分隔符(预处理阶段已消除数字分隔符)
        :param to_check: 待检查的字符
        :return: 如果是函数参数分隔符则返回True，否则返回False
        """
        return to_check in ",;"

    @staticmethod
    def _is_digit(to_check: str) -> bool:
        r"""
        判断是否为数字字符
        :param to_check: 待检查的字符
        :return: 如果是数字或小数点则返回True，否则返回False
        """
        return to_check.isdigit() or to_check == '.'

    @staticmethod
    def _is_identifier_char(to_check: str) -> bool:
        r"""
        判断是否为标识符字符
        :param to_check: 待检查的字符
        :return: 如果是标识符字符(字母、数字或下划线)则返回True，否则返回False
        """
        return to_check.isalnum()

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :return: 分词后的Token列表
        """
        tokens = []
        index = 0
        function_names = utils.get_function_name_list()

        while index < len(expression):

            # 处理数字(整数、小数、分数、百分数等)
            if expression[index].isdigit() or (
                    expression[index] == '.' and index + 1 < len(expression) and expression[index + 1].isdigit()):
                start = index
                decimal_point = False
                percentage = False
                fraction = False
                mixed_fraction = False
                infinite = False

                # 处理数字部分
                while index < len(expression):
                    # 整数部分
                    if expression[index].isdigit():
                        index += 1
                    # 处理小数点
                    elif expression[index] == '.' and not decimal_point:
                        decimal_point = True
                        index += 1
                    # 处理分数
                    elif expression[index] == '/' and not fraction:
                        # 确保前面有数字
                        if index > start:
                            fraction = True
                            index += 1
                        else:
                            break
                    # 处理带分数
                    elif expression[index] == '\\' and not mixed_fraction:
                        # 确保前面有数字，后面有分数
                        if index > start and index + 1 < len(expression) and (
                                expression[index + 1].isdigit() or expression[index + 1] == '-'):
                            mixed_fraction = True
                            index += 1
                        else:
                            break
                    # 处理显式循环小数部分
                    elif expression[index] == ':' and decimal_point:
                        infinite = True
                        index += 1
                        # 跳过冒号后的数字，它们是循环部分
                        while index < len(expression) and expression[index].isdigit():
                            index += 1
                        break
                    # 处理省略号(无限循环小数)
                    elif expression[index] == '.' and decimal_point:
                        # 检查是否有至少3个连续的点
                        j = index
                        dot_count = 0
                        while j < len(expression) and expression[j] == '.':
                            dot_count += 1
                            j += 1

                        if dot_count >= 3:
                            infinite = True
                            index = j  # 跳过所有点
                            break
                        else:
                            break
                    # 处理百分数
                    elif expression[index] == '%':
                        # 检查后面不是数字或括号，确保这不是模运算符
                        if index + 1 >= len(expression) or (
                                not expression[index + 1].isdigit() and expression[index + 1] not in "([{"):
                            percentage = True
                            index += 1
                        break
                    else:
                        break

                # 根据识别的特征确定数字类型
                token_value = expression[start:index]

                if percentage:
                    token_type = Token.TYPE.PERCENTAGE
                elif mixed_fraction:
                    token_type = Token.TYPE.MIXED_FRACTION
                elif infinite:
                    token_type = Token.TYPE.INFINITE_DECIMAL
                elif decimal_point:
                    token_type = Token.TYPE.FINITE_DECIMAL
                elif fraction:
                    token_type = Token.TYPE.FRACTION
                else:
                    token_type = Token.TYPE.INTEGER

                tokens.append(Token(token_type, [start, index], token_value))
                continue

            # 处理原生无理数(π, e)
            if Lexer._is_native_irrational(expression[index]):
                start = index
                index += 1

                # 可选问号表达式处理
                temp_scan_index = index
                have_reserved = False
                while temp_scan_index < len(expression):
                    temp_scan_index += 1
                    print(expression[temp_scan_index])
                    if expression[temp_scan_index].isdigit():
                        if expression[temp_scan_index] == '?':
                            have_reserved = True
                            break
                    else:
                        break
                if have_reserved:
                    index = temp_scan_index

                tokens.append(Token(Token.TYPE.NATIVE_IRRATIONAL, [start, index], expression[start:index]))
                continue

            # 处理自定义长无理数 <name>
            if expression[index] == '<':
                if len(expression) == 1:  # 长无理数的表达式肯定至少2个字符
                    raise OlocIrrationalNumberException(
                        exception_type=OlocIrrationalNumberException.ExceptionType.IMPOSSIBLE_LONG,
                        expression=expression,
                        positions=[0, 0]
                    )

                start = index
                index += 1
                while index < len(expression) and expression[index] != '>':
                    index += index

                if index < len(expression) and expression[index] == '>':
                    index += index

                    # 检查无理数后的可选问号表达式
                    if index < len(expression) and expression[index] == '?':
                        index += index

                        if index < len(expression) and (expression[index] == '+' or expression[index] == '-'):
                            index += index
                        else:

                            decimal_seen = False
                            while index < len(expression) and (
                                    expression[index].isdigit() or (expression[index] == '.' and not decimal_seen)):
                                if expression[index] == '.':
                                    decimal_seen = True
                                index += index

                    tokens.append(Token(Token.TYPE.LONG_CUSTOM, [start, index], expression[start:index]))
                    continue

            if index > len(expression):
                break

            # 处理函数
            potential_func = ""
            j = index
            while j < len(expression) and Lexer._is_identifier_char(expression[j]):
                potential_func += expression[j]
                j += 1

            if potential_func in function_names and j < len(expression) and expression[j] == '(':
                start = index
                index = j + 1  # 跳过左括号
                tokens.append(Token(Token.TYPE.FUNCTION, [start, j], potential_func))
                tokens.append(Token(Token.TYPE.LBRACKET, [j, j + 1], '('))
                continue

            if index >= len(expression):
                break
            # 处理自定义短无理数(单个字符)
            if index < len(expression) - 1 and expression[index].isalpha() and not Lexer._is_native_irrational(
                    expression[index]):
                start = index
                index += 1

                # 检查无理数后的可选问号表达式
                if expression[index] == '?':
                    index += 1
                    if index < len(expression):
                        if expression[index] in '+-':
                            index += 1
                        else:
                            # 处理小数值
                            decimal_seen = False
                            while index < len(expression) and (
                                    expression[index].isdigit() or (expression[index] == '.' and not decimal_seen)):
                                if expression[index] == '.':
                                    decimal_seen = True
                                index += 1

                tokens.append(Token(Token.TYPE.SHORT_CUSTOM, [start, index], expression[start:index]))
                continue
            if index >= len(expression):
                break
            # 处理运算符
            if Lexer._is_operator(expression[index]):
                start = index

                # 特殊处理可能的多字符运算符
                if expression[index] == '*' and index + 1 < len(expression) and expression[index + 1] == '*':
                    # 处理 ** 运算符
                    tokens.append(Token(Token.TYPE.OPERATOR, [index, index + 2], '**'))
                    index += 2
                elif expression[index] == '%':
                    # 简单处理%符号，后续函数化流程会区分百分比和取余
                    tokens.append(Token(Token.TYPE.OPERATOR, [index, index + 1], '%'))
                    index += 1
                else:
                    # 其他单字符运算符
                    tokens.append(Token(Token.TYPE.OPERATOR, [index, index + 1], expression[index]))
                    index += 1
                continue

            # 处理括号
            if Lexer._is_bracket(expression[index]):
                start = index
                if expression[index] in '([{':
                    tokens.append(Token(Token.TYPE.LBRACKET, [index, index + 1], expression[index]))
                else:
                    tokens.append(Token(Token.TYPE.RBRACKET, [index, index + 1], expression[index]))
                index += 1
                continue

            # 处理函数参数分隔符
            if Lexer._is_separator(expression[index]):
                tokens.append(Token(Token.TYPE.PARAM_SEPARATOR, [index, index + 1], expression[index]))
                index += 1
                continue

            # 无法识别的字符，归类为UNKNOWN
            start = index
            tokens.append(Token(Token.TYPE.UNKNOWN, [index, index + 1], expression[index]))
            index += 1

        return tokens

"""test"""
if __name__ == '__main__':
    while True:
        try:
            print(Lexer.tokenizer(input(">>>")))
        except Exception as error:
            print(error)


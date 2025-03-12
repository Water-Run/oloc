r"""
:author: WaterRun
:date: 2025-03-12
:file: lexer.py
:description: Oloc lexer
"""

import utils
import evaluator

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

    def get_exception_type(self) -> OlocInvalidTokenException.ExceptionType:
        r"""
        返回对应的OlocInvalidTokenException.ExceptionType类型
        :return:
        """
        mapping = {
            Token.TYPE.PERCENTAGE: OlocInvalidTokenException.ExceptionType.INVALID_PERCENTAGE,
            Token.TYPE.MIXED_FRACTION: OlocInvalidTokenException.ExceptionType.INVALID_MIXED_FRACTION,
            Token.TYPE.INFINITE_DECIMAL: OlocInvalidTokenException.ExceptionType.INVALID_INFINITE_DECIMAL,
            Token.TYPE.FINITE_DECIMAL: OlocInvalidTokenException.ExceptionType.INVALID_FINITE_DECIMAL,
            Token.TYPE.INTEGER: OlocInvalidTokenException.ExceptionType.INVALID_INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL: OlocInvalidTokenException.ExceptionType.INVALID_NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM: OlocInvalidTokenException.ExceptionType.INVALID_SHORT_CUSTOM_IRRATIONAL,
            Token.TYPE.LONG_CUSTOM: OlocInvalidTokenException.ExceptionType.INVALID_LONG_CUSTOM_IRRATIONAL,
            Token.TYPE.OPERATOR: OlocInvalidTokenException.ExceptionType.INVALID_OPERATOR,
            Token.TYPE.LBRACKET: OlocInvalidTokenException.ExceptionType.INVALID_BRACKET,
            Token.TYPE.RBRACKET: OlocInvalidTokenException.ExceptionType.INVALID_BRACKET,
            Token.TYPE.FUNCTION: OlocInvalidTokenException.ExceptionType.INVALID_FUNCTION,
            Token.TYPE.PARAM_SEPARATOR: OlocInvalidTokenException.ExceptionType.INVALID_PARAM_SEPARTOR,
            Token.TYPE.UNKNOWN: OlocInvalidTokenException.ExceptionType.UNKNOWN_TOKEN,
        }
        return mapping[self.TYPE]

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

    def _check_mixed_fraction(self) -> bool:
        r"""
        检查带分数类型的Token的合法性
        :return: 是否合法
        """
        if '\\' in self.value and '/' in self.value:
            parts = self.value.split('\\')
            if len(parts) == 2:
                integer_part, fraction_part = parts
                if integer_part.isdigit():
                    fraction_parts = fraction_part.split('/')
                    if len(fraction_parts) == 2 and all(p.isdigit() for p in fraction_parts):
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
        if self.value.startswith(('π', '𝑒')) and self.value.endswith('?'):
            middle_part = self.value[1:-1]
            if middle_part.isdigit():
                return True
        return False

    def _check_short_custom(self) -> bool:
        r"""
        检查自定义短无理数类型的Token的合法性
        :return: 是否合法
        """
        if self.value.endswith("?"):
            if len(self.value) <= 2:
                return False
            short_irrational = self.value[0]
            convert_param = self.value[1:-1]
            if convert_param[0] in "+-":
                if len(convert_param) > 1 and not Lexer.is_str_a_number(convert_param[1:]):
                    return False
        else:
            short_irrational = self.value
        if len(short_irrational) != 1 or short_irrational in set(utils.get_symbol_mapping_table().keys()):
            return False
        return True

    def _check_long_custom(self) -> bool:
        r"""
        检查自定义长无理数类型的Token的合法性
        :return: 是否合法
        """
        if not self.value.startswith("<") or (not self.value.endswith(">") and not self.value.endswith("?")):
            return False

        if self.value.endswith(">"):
            return True

        convert_param = self.value[self.value.rindex('>') + 1:len(self.value) - 1]
        if not convert_param:
            return False

        if convert_param[0] in "+-":
            return len(convert_param) > 1 and Lexer.is_str_a_number(convert_param[1:])

        return Lexer.is_str_a_number(convert_param)

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


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.tokens = []

    def _convert_token_flow(self) -> None:
        r"""
        将表达式转为Token流,并检查Token的合法性
        :return: None
        """
        self.tokens = Lexer.tokenizer(self.expression)
        for token in self.tokens:
            if not token.is_legal:
                raise OlocInvalidTokenException(
                    exception_type=token.get_exception_type(),
                    expression=self.expression,
                    positions=token.range,
                    token_content=token.value if token else "",
                )

    def _formal_elimination_complement(self) -> None:
        r"""
        消除表达式中的一些特殊形式.包括数字分隔符,括号化简,正负号消除,并补全表达式中的一些可省略的特殊形式.包括隐式的乘法符号
        :return: None
        :raise OlocNumberSeparatorException: 检测到数字分隔符不合法
        """

    def _fractionalization(self) -> None:
        r"""
        将表达式Token流中的各种数字转换为分数
        :return: None
        """

        def _convert_finite_decimal(finite_decimal: Token) -> [Token, Token, Token]:
            r"""
            将有限小数转为分数
            :param finite_decimal: 待转换的有限小数
            :return: 转换后的分数
            """
            integer_part, decimal_part = finite_decimal.split('.')

            numerator = int(integer_part + decimal_part)
            denominator = 10 ** len(decimal_part)

            if int(integer_part) < 0:
                numerator = -numerator

            fraction = f"{numerator}/{denominator}"

            return fraction

        def _convert_infinite_decimal(infinite_decimal: Token) -> [Token, Token, Token]:
            r"""
            将无限循环小数转为分数
            :param infinite_decimal: 待转换的无限小数
            :return: 转换后的分数
            """

            def _spilt_decimal_parts(process_decimal: str) -> list[str, str]:
                r"""
                切分无限循环小数中重复的部分和有限小数部分
                :param process_decimal: 待查找的无限循环小数
                :return: 一个字符串列表, 第一项是查找到的重复部分, 第二项是移除重复部分后的有限小数
                """
                # 处理结尾有点号的情况
                if '.' in process_decimal and process_decimal.count('.') > 1:
                    # 移除结尾的所有点号
                    base_number = process_decimal.rstrip('.')

                    # 分离整数和小数部分
                    integer_part, decimal_part = base_number.split('.')

                    # 最后一位数字是循环部分
                    if decimal_part:
                        repeat_part = decimal_part[-1]
                        finite_part = integer_part + "." + decimal_part[:-1]
                    else:
                        # 如果没有小数部分，默认循环部分为0
                        repeat_part = "0"
                        finite_part = integer_part + ".0"

                    return [repeat_part, finite_part]

                # 处理显式声明循环部分的情况（使用:分隔）
                if ':' in process_decimal:
                    base_number, repeat_part = process_decimal.split(':')

                    if '.' in base_number:
                        integer_part, decimal_part = base_number.split('.')
                        finite_part = integer_part + "." + decimal_part
                    else:
                        # 如果基数部分没有小数点，加上.0
                        finite_part = base_number + ".0"

                    return [repeat_part, finite_part]

                # 默认情况：不应该进入此分支，因为输入保证是循环小数
                return ["", process_decimal]

            def _fraction_from_parts(repeat_part: str, finite_part: str) -> str:
                r"""
                根据循环部分和有限部分计算分数形式
                :param repeat_part: 循环部分
                :param finite_part: 有限部分
                :return: 分数字符串
                """
                # 分解有限部分
                if '.' in finite_part:
                    integer_str, decimal_str = finite_part.split('.')
                else:
                    integer_str, decimal_str = finite_part, '0'

                # 将整数部分转为整数
                integer_value = int(integer_str) if integer_str else 0

                # 计算分母：循环部分产生的分母是9的乘积
                denominator = int('9' * len(repeat_part))

                # 如果有限小数部分非空，需要将循环部分乘以适当的因子
                if decimal_str:
                    denominator = denominator * (10 ** len(decimal_str))

                # 计算分子
                numerator = 0

                # 处理整数部分
                if integer_value:
                    numerator += integer_value * denominator

                # 处理有限小数部分
                if decimal_str:
                    numerator += int(decimal_str) * int('9' * len(repeat_part))

                # 处理循环部分
                if repeat_part:
                    numerator += int(repeat_part)

                # 返回分数形式
                return f"{numerator}/{denominator}"

            # 主函数逻辑
            parts = _spilt_decimal_parts(infinite_decimal)
            repeat_part, finite_part = parts[0], parts[1]

            # 计算分数
            fraction = _fraction_from_parts(repeat_part, finite_part)

            # 调用化简函数
            return fraction

        def _convert_percentage(percentage: Token) -> [Token, Token, Token]:
            r"""
            将百分数转为小数
            :param percentage: 待转换的百分数，例如"12.5%"
            :return: 转换后的小数字符串，例如"0.125"
            """
            # 去掉百分号
            percentage = percentage[:-1]

            # 检查是否包含小数点，确保分割操作不会出错
            if '.' not in percentage:
                percentage += '.0'

            integer_part, decimal_part = percentage.split('.')

            # 根据整数部分长度调整小数点位置
            if integer_part == '0':
                percentage = '0.00' + decimal_part
            elif len(integer_part) == 1:
                percentage = '0.0' + integer_part + decimal_part
            elif len(integer_part) == 2:
                percentage = '0.' + integer_part + decimal_part
            else:
                decimal_point_pos = len(integer_part) - 2
                percentage = integer_part[:decimal_point_pos] + '.' + integer_part[decimal_point_pos:] + decimal_part

            percentage = percentage.rstrip('0')
            if percentage.endswith('.'):
                percentage = percentage[:-1]

            return percentage if '.' not in percentage else _convert_finite_decimal(percentage)

        def _convert_mix_fraction(mix_fraction: Token) -> [Token, Token, Token]:
            r"""
            将带分数转为分数
            :param mix_fraction: 待转换的带分数
            :return: 转换后的分数
            """
            # 分割带分数的整数部分和分数部分
            parts = mix_fraction.split('\\')

            # 获取整数部分
            integer_part = parts[0]

            # 获取分数部分
            fraction_part = parts[1]

            # 分割分子和分母
            numerator, denominator = fraction_part.split('/')

            # 将整数部分转换为同分母的分数
            integer_as_fraction_numerator = int(integer_part) * int(denominator)

            # 计算最终的分子
            final_numerator = integer_as_fraction_numerator + int(numerator)

            # 构建最终的分数字符串
            final_fraction = f"{final_numerator}/{denominator}"

            return final_fraction

        temp_tokens = Lexer.tokenizer(self.expression)
        fractionalized_tokens = []

        convert_num_types = [
            Token.TYPE.PERCENTAGE,
            Token.TYPE.MIXED_FRACTION,
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INFINITE_DECIMAL,
        ]

        token_fractionalized = []
        for temp_token in temp_tokens:
            if (convert_type := temp_token.type) in convert_num_types:
                match convert_type:
                    case Token.TYPE.MIXED_FRACTION:
                        token_fractionalized = _convert_mix_fraction(temp_token)
                    case Token.TYPE.FINITE_DECIMAL:
                        token_fractionalized = _convert_finite_decimal(temp_token)
                    case Token.TYPE.INFINITE_DECIMAL:
                        token_fractionalized = _convert_infinite_decimal(temp_token)
                    case Token.TYPE.PERCENTAGE:
                        token_fractionalized = _convert_percentage(temp_token)
                fractionalized_tokens += evaluator.Evaluator.simplify(token_fractionalized)
            else:
                fractionalized_tokens += temp_token

    def _function_conversion(self) -> None:
        r"""
        根据函数转换表进行函数转换
        :return: None
        """

    def execute(self):
        r"""
        执行分词器
        :return: None
        """

        self._convert_token_flow()
        self._formal_elimination_complement()
        self._fractionalization()

    """
    静态方法
    """

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :return: 分词后的Token列表
        """
        function_names = utils.get_function_name_list()
        symbol_mapping_table = utils.get_symbol_mapping_table()

        mark_list = [Token.TYPE.UNKNOWN for _ in range(len(expression))]

        # 逐字符扫描
        for index, unit in enumerate(zip(expression, mark_list)):
            unit_char = unit[0]
            unit_type = unit[1]

            if unit_type != Token.TYPE.UNKNOWN:
                ...

        token_flow = []  # 结果的Token流

    @staticmethod
    def is_str_a_number(number: str) -> bool:
        r"""
        检查对应的字符串数字是否是数字(整数,或有限小数)
        :param number: 待判断的数字字符串
        :return: 是否是数字
        """
        if '.' in number:
            number_parts = number.split('.')
            if not 1 <= len(number_parts) <= 2:
                return False
            number = "".join(number_parts)
        return number.isdigit()


"""test"""
if __name__ == '__main__':

    while True:
        try:
            tests = [
                [Token.TYPE.LONG_CUSTOM, "<>>"],
                [Token.TYPE.LONG_CUSTOM, "<12313>"],
                [Token.TYPE.LONG_CUSTOM, "12312>"],
                [Token.TYPE.LONG_CUSTOM, "<11>?"],
                [Token.TYPE.LONG_CUSTOM, "<11>+?"],
                [Token.TYPE.LONG_CUSTOM, "<11>-1?"],
                [Token.TYPE.LONG_CUSTOM, "<11>+0.92514?"],
                [Token.TYPE.LONG_CUSTOM, "<abadad>+?"],
                [Token.TYPE.LONG_CUSTOM, "<11adada>+ad?"],
                [Token.TYPE.LONG_CUSTOM, "<11>+?123"],
                [Token.TYPE.LONG_CUSTOM, "<11>123?"],
                [Token.TYPE.LONG_CUSTOM, "<11>0.55?"],
            ]
            for test in tests:
                test_token = Token(test[0], test[1])
                print(f"{test_token.value} {test_token.is_legal}")
        except Exception as error:
            print(error)
        input(">>>>")

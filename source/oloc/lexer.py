r"""
:author: WaterRun
:date: 2025-03-14
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


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.tokens: list[Token] = []

    def _convert_token_flow(self) -> None:
        r"""
        将表达式转为Token流,并检查Token的合法性
        :return: None
        """
        self.tokens = Lexer.tokenizer(self.expression)
        for check_token in self.tokens:
            if not check_token.is_legal:
                raise OlocInvalidTokenException(
                    exception_type=check_token.get_exception_type(),
                    expression=self.expression,
                    positions=list(range(*[check_token.range[0], check_token.range[1]])),
                    token_content=check_token.value if check_token else "",
                )

    def _update(self) -> None:
        r"""
        刷新表达式及Token的下标
        :return:
        """
        # 清空表达式和起始下标
        self.expression = ""
        start_index = 0

        # 遍历所有Token，拼接表达式并检查下标连续性
        for index, token in enumerate(self.tokens):
            # 拼接表达式
            self.expression += token.value

            # 如果是第一个Token，直接设置其下标
            if index == 0:
                token.range = [start_index, start_index + len(token.value)]
                start_index = token.range[1]
                continue

            # 检查当前Token和前一个Token的下标连续性
            previous_token = self.tokens[index - 1]
            if previous_token.range[1] != token.range[0]:
                # 下标不连续，重新分配当前Token及后续Token的下标
                token.range = [start_index, start_index + len(token.value)]
            else:
                # 下标连续，保持当前下标
                token.range = [previous_token.range[1], previous_token.range[1] + len(token.value)]

            # 更新起始下标
            start_index = token.range[1]

    def _formal_complementation(self) -> None:
        r"""
        补全表达式中的一些特殊形式,如被省略的乘号
        :return: None
        """

        # 定义数字和无理数的类型集合
        NUMBERS = {
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INFINITE_DECIMAL,
            Token.TYPE.PERCENTAGE,
            Token.TYPE.INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.LONG_CUSTOM
        }

        IRRATIONALS = {
            Token.TYPE.LONG_CUSTOM,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.NATIVE_IRRATIONAL
        }

        # 遍历 Token 列表
        index = 0
        while index < len(self.tokens) - 1:
            current_token = self.tokens[index]
            next_token = self.tokens[index + 1]

            # 情况 1: 数字后接 (
            if current_token.type in NUMBERS and next_token.type == Token.TYPE.LBRACKET:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 情况 2: 无理数参数后接 (
            elif current_token.type == Token.TYPE.IRRATIONAL_PARAM and next_token.type == Token.TYPE.LBRACKET:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 情况 3: ) 后接数字
            elif current_token.type == Token.TYPE.RBRACKET and next_token.type in NUMBERS:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 情况 4: 无理数后接无理数
            elif current_token.type in IRRATIONALS and next_token.type in IRRATIONALS:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 情况 5: 数字后接无理数
            elif current_token.type in NUMBERS and next_token.type in IRRATIONALS:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 情况 6: 无理数后接数字
            elif current_token.type in IRRATIONALS and next_token.type in NUMBERS:
                self.tokens = self.tokens[:index + 1] + [Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                                                            index + 1:]

            # 前进到下一个 Token
            index += 1
        self._update()

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
            :return: 转换后的分数, 依次为分子, 分数线, 分母
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

        temp_tokens = Lexer.tokenizer(self.expression)
        fractionalized_tokens = []

        convert_num_types = [
            Token.TYPE.PERCENTAGE,
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INFINITE_DECIMAL,
        ]

        tokens_fractionalized: list[Token] = []
        for temp_token in temp_tokens:
            if (convert_type := temp_token.type) in convert_num_types:
                match convert_type:
                    case Token.TYPE.FINITE_DECIMAL:
                        tokens_fractionalized = _convert_finite_decimal(temp_token)
                    case Token.TYPE.INFINITE_DECIMAL:
                        tokens_fractionalized = _convert_infinite_decimal(temp_token)
                    case Token.TYPE.PERCENTAGE:
                        tokens_fractionalized = _convert_percentage(temp_token)
                fractionalized_tokens += evaluator.Evaluator.simplify(tokens_fractionalized)
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
        self._formal_complementation()

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

        """
        模块标记
        """

        # 标记自定义长无理数
        for index, char in enumerate(expression):
            # 已经标记过的跳过

            if index > 0 and mark_list[index - 1] == Token.TYPE.LONG_CUSTOM:
                continue

            if char == '<':

                # 单个左尖括号是错误的
                if index == len(expression) - 1:
                    raise OlocIrrationalNumberException(
                        exception_type=OlocIrrationalNumberException.EXCEPTION_TYPE.MISMATCH_LONG_LEFT_SIGN,
                        expression=expression,
                        positions=[index, index],
                    )

                # 查找匹配的右尖括号
                right_bracket_index = None
                for i in range(index + 1, len(expression)):
                    if expression[i] == '>':
                        right_bracket_index = i
                        break

                # 如果没找到匹配的右尖括号，抛出异常
                if right_bracket_index is None:
                    raise OlocIrrationalNumberException(
                        exception_type=OlocIrrationalNumberException.EXCEPTION_TYPE.MISMATCH_LONG_LEFT_SIGN,
                        expression=expression,
                        positions=[index, index],
                    )

                # 标记整个范围为LONG_CUSTOM
                for i in range(index, right_bracket_index + 1):
                    mark_list[i] = Token.TYPE.LONG_CUSTOM

        # 标记无理数参数
        for index, char in enumerate(expression):
            if char == "?":
                # 记录当前 ? 的索引并初始化索引列表
                irrational_param_index_list = [index]

                # 开始向前扫描
                find_dot = False

                for scan_index in range(index - 1, -1, -1):  # 从当前索引向前遍历
                    scan_char = expression[scan_index]

                    if scan_char.isdigit() or scan_char in {".", "+", "-"}:
                        irrational_param_index_list.append(scan_index)
                        if scan_char == ".":
                            if find_dot:  # 如果已经遇到过小数点，停止扫描
                                break
                            find_dot = True
                        elif scan_char in {"+", "-"}:  # 遇到加号或减号，停止扫描
                            break
                    else:  # 非数字、非符号直接停止
                        break

                # 标记所有相关索引为 IRRATIONAL_PARAM
                for irrational_index in irrational_param_index_list:
                    mark_list[irrational_index] = Token.TYPE.IRRATIONAL_PARAM

        for func_name in function_names:
            start = 0
            func_len = len(func_name)

            # 在表达式中查找函数名
            while (index := expression.find(func_name, start)) != -1:
                end_index = index + func_len
                # 标记匹配范围内的字符为 FUNCTION，不再检查前后字符
                for i in range(index, end_index):
                    mark_list[i] = Token.TYPE.FUNCTION

                # 更新查找的起始位置，避免重复匹配
                start = end_index

        # 标记数字
        for index, char in enumerate(expression):

            # 如果当前索引已经处理过，则跳过
            if mark_list[index] != Token.TYPE.UNKNOWN:
                continue

            # 处理数字
            if char.isdigit():
                mode = Token.TYPE.INTEGER  # 默认模式为整数
                attempt_index = index
                digit_index_range_list = [index]  # 保存数字索引范围
                find_decimal_point = False  # 是否找到小数点
                is_infinite_decimal = False  # 是否为无限小数

                while attempt_index + 1 < len(expression):
                    attempt_index += 1
                    current_char = expression[attempt_index]

                    if current_char == "%" and mode in [Token.TYPE.INTEGER, Token.TYPE.FINITE_DECIMAL]:
                        if attempt_index + 1 < len(expression) and expression[attempt_index + 1] not in ["+", "-", "*", "/",
                                                                                                 "^", "%", "|", ")", "]", "}"]:
                            break
                        mode = Token.TYPE.PERCENTAGE
                        digit_index_range_list.append(attempt_index)
                        break

                    # 处理小数点
                    if current_char == ".":
                        if find_decimal_point:  # 如果已经找到过小数点，检查是否为无限小数
                            # 检查是否为无限循环小数
                            next_char_index = attempt_index + 1
                            if next_char_index < len(expression) and expression[next_char_index] == ".":
                                is_infinite_decimal = True
                                mode = Token.TYPE.INFINITE_DECIMAL
                                digit_index_range_list.append(attempt_index)  # 将当前点加入标注范围
                                param_index = attempt_index + 1
                                point_count = 1  # 记录连续点的数量

                                while param_index < len(expression):
                                    if expression[param_index] == ".":
                                        point_count += 1
                                        digit_index_range_list.append(param_index)  # 将点加入标注范围
                                    else:
                                        break  # 遇到非点字符时退出
                                    param_index += 1

                                if not 6 <= point_count <= 3:
                                    break

                                # 确保最后一个点也被标记
                                attempt_index = param_index - 1
                                continue
                            else:
                                break  # 如果不是无限小数，退出
                        find_decimal_point = True
                        mode = Token.TYPE.FINITE_DECIMAL
                        digit_index_range_list.append(attempt_index)  # 将小数点加入标注范围
                        continue

                    # 处理显式标注的无理数
                    if current_char == ":" and find_decimal_point:
                        is_infinite_decimal = True
                        digit_index_range_list.append(attempt_index)
                        next_index = attempt_index + 1
                        while next_index < len(expression):
                            if not expression[next_index].isdigit():
                                break
                            digit_index_range_list.append(next_index)
                            next_index += 1

                    # 处理数字字符
                    if current_char.isdigit():
                        digit_index_range_list.append(attempt_index)
                    else:
                        break

                # 如果当前是无限小数，将所有标记为 INFINITE_DECIMAL
                if is_infinite_decimal:
                    mode = Token.TYPE.INFINITE_DECIMAL

                # 更新标记列表
                for digit_index in digit_index_range_list:
                    if 0 <= digit_index < len(mark_list):  # 确保索引合法
                        mark_list[digit_index] = mode

        r"""
        逐字符扫描
        """
        # 逐字符扫描
        for index, unit in enumerate(zip(expression, mark_list)):
            unit_char: str = unit[0]
            unit_type = unit[1]

            # 已经标记过
            if unit_type != Token.TYPE.UNKNOWN:
                continue

            # 标记函数参数分隔符
            if unit_char in ";,":
                mark_list[index] = Token.TYPE.PARAM_SEPARATOR

            # 标记括号
            if unit_char in "{[(":
                mark_list[index] = Token.TYPE.LBRACKET
                continue
            if unit_char in ")]}":
                mark_list[index] = Token.TYPE.RBRACKET
                continue

            # 标记非数字
            if unit_char in ["π", "𝑒"]:
                mark_list[index] = Token.TYPE.NATIVE_IRRATIONAL
                continue

            if unit_char in symbol_mapping_table.keys():
                mark_list[index] = Token.TYPE.OPERATOR
                continue
            else:
                mark_list[index] = Token.TYPE.SHORT_CUSTOM
                continue

        """
        合并Token
        """
        tokens = []  # 最终生成的 Token 列表
        current_type = None  # 当前正在处理的 Token 类型
        current_value = ""  # 当前正在构造的 Token 值
        current_start = 0  # 当前 Token 的起始索引

        # 需要合并的 Token 类型
        mergeable_types = {
            Token.TYPE.PERCENTAGE,
            Token.TYPE.INFINITE_DECIMAL,
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INTEGER,
            Token.TYPE.LONG_CUSTOM,
            Token.TYPE.IRRATIONAL_PARAM,
            Token.TYPE.FUNCTION,
            Token.TYPE.UNKNOWN,
        }

        for i, (char, token_type) in enumerate(zip(expression, mark_list)):
            if current_type is None:  # 初始化第一个 Token
                current_type = token_type
                current_value = char
                current_start = i
            elif token_type == current_type and token_type in mergeable_types:  # 如果类型相同且可合并，继续合并
                current_value += char
            else:  # 遇到不同类型的 Token，保存当前 Token，并开始新的 Token
                tokens.append(Token(current_type, current_value, [current_start, i]))
                current_type = token_type
                current_value = char
                current_start = i

        # 处理最后一个 Token
        if current_type is not None:
            tokens.append(Token(current_type, current_value, [current_start, len(expression)]))

        return tokens


"""test"""
if __name__ == '__main__':
    import preprocessor

    import simpsave as ss

    from time import time
    tests = ss.read("test_cases", file="./data/olocconfig.ini")
    start = time()
    for test in tests:
        try:
            preprocess = preprocessor.Preprocessor(test)
            preprocess.execute()
            print(test, end=" => ")
            lexer = Lexer(preprocess.expression)
            lexer.execute()
            for token in lexer.tokens:
                ... # debug
                print(token.value, end=" ")
            print()
        except Exception as error:
            print(f"\n\n\n========\n\n{error}\n\n\n")
    print(f"Run {len(tests)} in {time() - start}")

    while True:
        try:
            preprocess = preprocessor.Preprocessor(input(">>>"))
            preprocess.execute()
            lexer = Lexer(preprocess.expression)
            lexer.execute()
            print(lexer.tokens)
            for token in lexer.tokens:
                print(token.value, end=" ")
        except Exception as error:
            print(error)

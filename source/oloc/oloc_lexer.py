r"""
:author: WaterRun
:date: 2025-04-03
:file: oloc_lexer.py
:description: Oloc lexer
"""

import time
from math import gcd

import oloc_utils as utils
from oloc_token import Token
from oloc_exceptions import *


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.tokens: list[Token] = []
        self.time_cost = -1

    def __repr__(self):
        result = (f"Lexer: \n"
                  f"expression: {self.expression}\n"
                  f"expression (spilt between token): ")
        for token in self.tokens:
            result += f"{token.value} "
        result += "\ntoken flow: \n"
        for index, token in enumerate(self.tokens):
            result += f"{index}\t{token}\n"
        result += f"time cost: {'(Not execute)' if self.time_cost == -1 else self.time_cost / 1000000} ms\n"
        return result

    def _convert_token_flow(self) -> None:
        r"""
        将表达式转为Token流,并检查Token的合法性
        :return: None
        """
        self.tokens = Lexer.tokenizer(self.expression)
        self._self_check()

    def _self_check(self) -> None:
        r"""
        Token流自检
        :raise OlocValueError: 如果Token不合法
        :return: None
        """
        for check_token in self.tokens:
            if not check_token.is_legal:
                raise OlocValueError(
                    exception_type=check_token.get_exception_type(),
                    expression=self.expression,
                    positions=list(range(*[check_token.range[0], check_token.range[1]])),
                    primary_info=check_token.value if check_token else "",
                )
            if check_token.type == Token.TYPE.LONG_CUSTOM and check_token.value.startswith('<__reserved'):
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.RESERVED_WORD_CONFLICT,
                    expression=self.expression,
                    positions=list(range(*[check_token.range[0], check_token.range[1]])),
                    primary_info=check_token.value,
                )

    def _formal_complementation(self) -> None:
        r"""
        补全表达式中的一些特殊形式,如被省略的乘号
        :return: None
        """

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

        def _add_multiply(add_index: int):
            r"""
            添加乘号至 Token 流
            :param add_index: 要添加乘号的位置
            """
            self.tokens = (
                    self.tokens[:add_index + 1]
                    + [Token(Token.TYPE.OPERATOR, "*", [add_index + 1, add_index + 2])]
                    + self.tokens[add_index + 1:]
            )

        token_index = 0
        while token_index < len(self.tokens) - 1:
            current_token = self.tokens[token_index]
            next_token = self.tokens[token_index + 1]

            conditions = [
                # 情况 1: 数字后接 (
                (lambda t1, t2: t1 in NUMBERS and t2 == Token.TYPE.LBRACKET),

                # 情况 2: 无理数参数后接 (
                (lambda t1, t2: t1 == Token.TYPE.IRRATIONAL_PARAM and t2 == Token.TYPE.LBRACKET),

                # 情况 3: ) 后接数字
                (lambda t1, t2: t1 == Token.TYPE.RBRACKET and t2 in NUMBERS),

                # 情况 4: 无理数后接无理数
                (lambda t1, t2: t1 in IRRATIONALS and t2 in IRRATIONALS),

                # 情况 5: 数字后接无理数
                (lambda t1, t2: t1 in NUMBERS and t2 in IRRATIONALS),

                # 情况 6: 无理数后接数字
                (lambda t1, t2: t1 in IRRATIONALS and t2 in NUMBERS),

                # 情况 7: 数字或右括号后接函数名
                (lambda t1, t2: t1 in list(NUMBERS) + [Token.TYPE.RBRACKET] and t2 == Token.TYPE.FUNCTION)
            ]

            if any(condition(current_token.type, next_token.type) for condition in conditions):
                _add_multiply(token_index)

            token_index += 1
            self.tokens, self.expression = Lexer.update(self.tokens)

    def _check_denominator(self, check_tokens: list[Token, Token, Token]) -> list[Token, Token, Token]:
        r"""
        检查传入的分数流(分子,分数线,分母)中的分母是否合法
        :param check_tokens: 被检查的Token
        :raise OlocCalculationError: 如果分母为0
        :return: 原样返回
        """
        if int(check_tokens[2].value) == 0:
            raise OlocCalculationError(
                exception_type=OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                expression=self.expression,
                positions=list(range(*[check_tokens[0].range[0], check_tokens[2].range[1]])),
                primary_info=check_tokens[0].value + check_tokens[1].value + check_tokens[2].value,
            )
        return check_tokens

    def _fractionalization(self) -> None:
        r"""
        将表达式Token流中的各种数字转换为分数
        :return: None
        """

        def _add_bracket(to_add: [Token, Token, Token]) -> [Token, Token, Token, Token, Token]:
            r"""
            为转换的结果添加括号
            :param to_add: 待添加的结果
            :return: 添加后的结果
            """
            return [Token(Token.TYPE.LBRACKET, "(", [0, 0])] + \
                to_add + [Token(Token.TYPE.RBRACKET, ")", [0, 0])]

        def _convert_finite_decimal(finite_decimal: Token) -> [Token, Token, Token]:
            r"""
            将有限小数转为分数
            :param finite_decimal: 待转换的有限小数
            :return: 转换后的分数Token流(分子,分数线,分母)
            """
            integer_part, decimal_part = finite_decimal.value.split('.')

            numerator = int(integer_part + decimal_part)
            denominator = 10 ** len(decimal_part)

            if int(integer_part) < 0:
                numerator = -numerator

            return [Token
                    (Token.TYPE.INTEGER,
                     str(numerator),
                     [finite_decimal.range[0], finite_decimal.range[0] + len(str(numerator))]
                     ),
                    Token(Token.TYPE.OPERATOR,
                          "/",
                          [finite_decimal.range[0] + len(str(numerator)) + 1,
                           finite_decimal.range[0] + len(str(numerator)) + 2]
                          ),
                    Token(Token.TYPE.INTEGER,
                          str(denominator),
                          [finite_decimal.range[0] + len(str(numerator)) + 2,
                           finite_decimal.range[0] + len(str(numerator)) + 2 + len(str(denominator))]
                          ),
                    ]

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
                        _repeat_part = decimal_part[-1]
                        _finite_part = integer_part + "." + decimal_part[:-1]
                    else:
                        # 如果没有小数部分，默认循环部分为0
                        _repeat_part = "0"
                        _finite_part = integer_part + ".0"

                    return [_repeat_part, _finite_part]

                # 处理显式声明循环部分的情况（使用:分隔）
                else:
                    base_number, _repeat_part = process_decimal.split(':')

                    if '.' in base_number:
                        integer_part, decimal_part = base_number.split('.')
                        _finite_part = integer_part + "." + decimal_part
                    else:
                        # 如果基数部分没有小数点，加上.0
                        _finite_part = base_number + ".0"

                    return [_repeat_part, _finite_part]

            def _fraction_from_parts(_repeat_part: str, _finite_part: str) -> list[Token, Token, Token]:
                r"""
                根据循环部分和有限部分计算分数形式
                :param _repeat_part: 循环部分
                :param _finite_part: 有限部分
                :return: 转换后的分数Token流(分子,分数线,分母)
                """
                # 分解有限部分
                if '.' in _finite_part:
                    integer_str, decimal_str = _finite_part.split('.')
                else:
                    integer_str, decimal_str = _finite_part, '0'

                # 将整数部分转为整数
                integer_value = int(integer_str) if integer_str else 0

                # 计算分母：循环部分产生的分母是9的乘积
                denominator = int('9' * len(_repeat_part))

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
                    numerator += int(decimal_str) * int('9' * len(_repeat_part))

                # 处理循环部分
                if _repeat_part:
                    numerator += int(_repeat_part)

                # 返回分数形式
                return [Token(Token.TYPE.INTEGER,
                              str(numerator),
                              [infinite_decimal.range[0], infinite_decimal.range[0] + len(str(numerator))]
                              ),
                        Token(Token.TYPE.OPERATOR,
                              "/",
                              [infinite_decimal.range[0] + len(str(numerator)) + 1,
                               infinite_decimal.range[0] + len(str(numerator)) + 2]
                              ),
                        Token(Token.TYPE.INTEGER,
                              str(denominator),
                              [infinite_decimal.range[0] + len(str(numerator)) + 2,
                               infinite_decimal.range[0] + len(str(numerator)) + 2 + len(str(denominator))]
                              ),
                        ]

            # 主函数逻辑
            infinite_decimal_str = infinite_decimal.value
            parts = _spilt_decimal_parts(infinite_decimal_str)
            repeat_part, finite_part = parts[0], parts[1]

            # 计算分数
            fraction = _fraction_from_parts(repeat_part, finite_part)

            # 调用化简函数
            return fraction

        def _convert_percentage(percentage: Token) -> [Token, Token, Token]:
            r"""
            将百分数转为小数
            :param percentage: 待转换的百分数
            :return: 转换后的小数字符串，例如"0.125"
            """
            # 去掉百分号
            percentage_str = percentage.value
            percentage_str = percentage_str[:-1]

            # 检查是否包含小数点，确保分割操作不会出错
            if '.' not in percentage_str:
                percentage_str += '.0'

            integer_part, decimal_part = percentage_str.split('.')

            # 根据整数部分长度调整小数点位置
            if integer_part == '0':
                percentage_str = '0.00' + decimal_part
            elif len(integer_part) == 1:
                percentage_str = '0.0' + integer_part + decimal_part
            elif len(integer_part) == 2:
                percentage_str = '0.' + integer_part + decimal_part
            else:
                decimal_point_pos = len(integer_part) - 2
                percentage_str = integer_part[:decimal_point_pos] + '.' + integer_part[
                                                                          decimal_point_pos:] + decimal_part

            percentage_str = percentage_str.rstrip('0')
            if percentage_str.endswith('.'):
                percentage_str = percentage_str[:-1]

            return [Token(Token.TYPE.INTEGER, percentage_str,
                          [percentage.range[0], percentage.range[0] + len(percentage_str)]),
                    Token(Token.TYPE.OPERATOR, "/",
                          [percentage.range[0] + len(percentage_str), percentage.range[0] + len(percentage_str) + 1]),
                    Token(Token.TYPE.INTEGER, "1",
                          [percentage.range[0] + len(percentage_str) + 1,
                           percentage.range[0] + len(percentage_str) + 2]),
                    ] if '.' not in percentage_str else _convert_finite_decimal(
                Token(Token.TYPE.FINITE_DECIMAL, percentage_str,
                      [percentage.range[0], percentage.range[0] + len(percentage_str)]))

        def _simplify_fraction(fraction_tokens: list[Token, Token, Token]) -> list[Token] or list[Token, Token, Token]:
            r"""
            化简传入的分数Token流
            :param fraction_tokens: 传入的分数Token流, 依次是整数, 分数线, 整数
            :return: 化简后的分数Token流, 或整数Token流(如果可能)
            """
            numerator = int(fraction_tokens[0].value)  # 分子
            denominator = int(fraction_tokens[2].value)  # 分母

            # 计算分子和分母的最大公约数
            divisor = gcd(numerator, denominator)

            # 化简分子和分母
            simplified_numerator = numerator // divisor
            simplified_denominator = denominator // divisor

            # 如果能化简为整数
            if simplified_denominator == 1:
                # 返回单个整数Token
                return [
                    Token(
                        Token.TYPE.INTEGER,
                        str(simplified_numerator),
                        [fraction_tokens[0].range[0], fraction_tokens[2].range[1]]  # 范围覆盖整个分数的原范围
                    )
                ]

            # 返回化简后的分数Token流
            return [
                Token(
                    Token.TYPE.INTEGER,
                    str(simplified_numerator),
                    [fraction_tokens[0].range[0], fraction_tokens[0].range[0] + len(str(simplified_numerator))]
                ),
                Token(
                    Token.TYPE.OPERATOR,
                    "/",
                    [fraction_tokens[0].range[0] + len(str(simplified_numerator)),
                     fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1]
                ),
                Token(
                    Token.TYPE.INTEGER,
                    str(simplified_denominator),
                    [fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1,
                     fraction_tokens[0].range[0] + len(str(simplified_numerator)) + 1 + len(
                         str(simplified_denominator))]
                )
            ]

        fractionalized_tokens = []

        convert_num_types = [
            Token.TYPE.PERCENTAGE,
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INFINITE_DECIMAL,
        ]

        tokens_to_fractionalized: list[Token] = []
        token_index = 0
        while token_index < len(self.tokens):
            temp_token = self.tokens[token_index]
            if (convert_type := temp_token.type) == Token.TYPE.INTEGER and \
                    token_index + 2 < len(self.tokens) and \
                    self.tokens[token_index + 1].value == "/" and \
                    self.tokens[token_index + 2].type == Token.TYPE.INTEGER:
                fractionalized_tokens += _simplify_fraction(
                    self._check_denominator([temp_token, self.tokens[token_index + 1], self.tokens[token_index + 2]]))
                token_index += 2
            elif convert_type in convert_num_types:
                match convert_type:
                    case Token.TYPE.FINITE_DECIMAL:
                        tokens_to_fractionalized = self._check_denominator(_convert_finite_decimal(temp_token))
                    case Token.TYPE.INFINITE_DECIMAL:
                        tokens_to_fractionalized = self._check_denominator(_convert_infinite_decimal(temp_token))
                    case Token.TYPE.PERCENTAGE:
                        tokens_to_fractionalized = self._check_denominator(_convert_percentage(temp_token))
                fractionalized_tokens += _add_bracket(_simplify_fraction(tokens_to_fractionalized))
            else:
                fractionalized_tokens += [temp_token]
            token_index += 1

        self.tokens, self.expression = Lexer.update(fractionalized_tokens)

    def _bracket_checking_harmonisation(self) -> None:
        """
        括号检查与统一化
        :raise OlocSyntaxError: 如果括号出现层级错误或不匹配
        :return: None
        """
        BRACKET_PRIORITY = {'(': 1, '[': 2, '{': 3, ')': 1, ']': 2, '}': 3}
        BRACKET_MATCH = {'(': ')', '[': ']', '{': '}', ')': '(', ']': '[', '}': '{'}

        stack = []

        for temp_token in self.tokens:
            if temp_token.type == Token.TYPE.LBRACKET:
                if stack and BRACKET_PRIORITY[temp_token.value] > BRACKET_PRIORITY[stack[-1][0]]:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.BRACKET_HIERARCHY_ERROR,
                        expression=self.expression,
                        positions=[temp_token.range[0]],
                        primary_info=temp_token.value
                    )
                stack.append((temp_token.value, temp_token.range[0], BRACKET_PRIORITY[temp_token.value]))

            elif temp_token.type == Token.TYPE.RBRACKET:
                if not stack:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.RIGHT_BRACKET_MISMATCH,
                        expression=self.expression,
                        positions=[temp_token.range[0]],
                        primary_info=temp_token.value
                    )

                last_left_bracket, last_position, last_priority = stack.pop()

                if BRACKET_MATCH[last_left_bracket] != temp_token.value:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.LEFT_BRACKET_MISMATCH,
                        expression=self.expression,
                        positions=[last_position],
                        primary_info=last_left_bracket
                    )

                if BRACKET_PRIORITY[last_left_bracket] != BRACKET_PRIORITY[temp_token.value]:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.BRACKET_HIERARCHY_ERROR,
                        expression=self.expression,
                        positions=[last_position],
                        primary_info=last_left_bracket
                    )

        if stack:
            last_left_bracket, last_position, _ = stack.pop()
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.LEFT_BRACKET_MISMATCH,
                expression=self.expression,
                positions=[last_position],
                primary_info=last_left_bracket
            )

        for bracket_token in self.tokens:
            if bracket_token.type == Token.TYPE.LBRACKET:
                bracket_token.value = '('
            elif bracket_token.type == Token.TYPE.RBRACKET:
                bracket_token.value = ')'

        self.tokens, self.expression = Lexer.update(self.tokens)
        self._self_check()

    def execute(self):
        r"""
        执行分词器
        :return: None
        """

        start_time = time.time_ns()
        self._convert_token_flow()
        self._formal_complementation()
        self._fractionalization()
        self._bracket_checking_harmonisation()
        self.time_cost = time.time_ns() - start_time

    """
    静态方法
    """

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :raise OlocSyntaxError: 如果无理数形式不合法
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
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.IRRATIONAL_BRACKET_MISMATCH,
                        expression=expression,
                        positions=[index, index],
                        primary_info='<',
                    )

                # 查找匹配的右尖括号
                right_bracket_index = None
                for i in range(index + 1, len(expression)):
                    if expression[i] == '>':
                        right_bracket_index = i
                        break

                # 如果没找到匹配的右尖括号，抛出异常
                if right_bracket_index is None:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.IRRATIONAL_BRACKET_MISMATCH,
                        expression=expression,
                        positions=[index, index],
                        primary_info='<',
                    )

                # 标记整个范围为LONG_CUSTOM
                for i in range(index, right_bracket_index + 1):
                    mark_list[i] = Token.TYPE.LONG_CUSTOM

        # 标记无理数参数
        for index, char in enumerate(expression):

            if mark_list[index] != Token.TYPE.UNKNOWN:
                continue

            if char == "?":
                # 记录当前 ? 的索引并初始化索引列表
                irrational_param_index_list = [index]

                # 开始向前扫描
                find_dot = False

                for scan_index in range(index - 1, -1, -1):  # 从当前索引向前遍历
                    scan_char = expression[scan_index]

                    if mark_list[scan_index] != Token.TYPE.UNKNOWN:
                        break

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

        # 标记函数
        for func_name in function_names:
            start = 0
            func_len = len(func_name)

            # 在表达式中查找函数名
            while (find_index := expression.find(func_name, start)) != -1:

                end_index = find_index + func_len

                if mark_list[find_index] != Token.TYPE.UNKNOWN:
                    start = end_index
                    continue

                for i in range(find_index, end_index):
                    mark_list[i] = Token.TYPE.FUNCTION

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
                        if attempt_index + 1 < len(expression) and expression[attempt_index + 1] not in ["+", "-", "*",
                                                                                                         "/",
                                                                                                         "^", "%", "|",
                                                                                                         ")", "]", "}",
                                                                                                         ",", ";"]:
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
            if unit_char in ",":
                mark_list[index] = Token.TYPE.PARAM_SEPARATOR
                continue

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

    @staticmethod
    def update(tokens: list[Token]) -> [list[Token], str]:
        r"""
        更新输入的 Token 流
        :return: 一个列表, 第一项是更新后的 Token 流, 第二项是表达式字符串
        """
        update_expression = ""
        start_index = 0
        result = []

        for token_index, process_token in enumerate(tokens):
            update_expression += process_token.value

            # 计算当前 token 的 range
            if token_index == 0:
                process_token.range = [start_index, start_index + len(process_token.value)]
            else:
                previous_token = tokens[token_index - 1]
                if previous_token.range[1] != process_token.range[0]:
                    process_token.range = [start_index, start_index + len(process_token.value)]
                else:
                    process_token.range = [previous_token.range[1], previous_token.range[1] + len(process_token.value)]

            # 无论如何都将当前 token 添加到结果列表
            result.append(process_token)
            start_index = process_token.range[1]

        return [result, update_expression]

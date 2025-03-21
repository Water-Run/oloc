r"""
:author: WaterRun
:date: 2025-03-21
:file: oloc_lexer.py
:description: Oloc lexer
"""

import re
import time
from enum import Enum
import oloc_utils as utils
from oloc_evaluator import Evaluator
from oloc_exceptions import *
from oloc_token import Token


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.tokens: list[Token] = []
        self.time_cost = -1

    def _convert_token_flow(self) -> None:
        r"""
        将表达式转为Token流,并检查Token的合法性
        :return: None
        :raise OlocInvalidTokenException: 如果Token不合法
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
            if check_token.type == Token.TYPE.LONG_CUSTOM and check_token.value.startswith('<__reserved'):
                raise OlocReservedWordException(
                    exception_type=OlocReservedWordException.EXCEPTION_TYPE.IS_RESERVED,
                    expression=self.expression,
                    positions=list(range(*[check_token.range[0], check_token.range[1]])),
                    conflict_str=check_token.value,
                )

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
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 情况 2: 无理数参数后接 (
            elif current_token.type == Token.TYPE.IRRATIONAL_PARAM and next_token.type == Token.TYPE.LBRACKET:
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 情况 3: ) 后接数字
            elif current_token.type == Token.TYPE.RBRACKET and next_token.type in NUMBERS:
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 情况 4: 无理数后接无理数
            elif current_token.type in IRRATIONALS and next_token.type in IRRATIONALS:
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 情况 5: 数字后接无理数
            elif current_token.type in NUMBERS and next_token.type in IRRATIONALS:
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 情况 6: 无理数后接数字
            elif current_token.type in IRRATIONALS and next_token.type in NUMBERS:
                self.tokens = self.tokens[:index + 1] + [
                    Token(Token.TYPE.OPERATOR, "*", [index + 1, index + 2])] + self.tokens[
                                                                               index + 1:]

            # 前进到下一个 Token
            index += 1
        self.tokens, self.expression = Lexer.update(self.tokens)

    def _check_denominator(self, check_tokens: list[Token, Token, Token]) -> list[Token, Token, Token]:
        r"""
        检查传入的分数流(分子,分数线,分母)中的分母是否合法
        :param check_tokens: 被检查的Token
        :raise OlocInvalidCalculationException: 如果分母为0
        :return: 原样返回
        """
        if int(check_tokens[2].value) == 0:
            raise OlocInvalidCalculationException(
                exception_type=OlocInvalidCalculationException.EXCEPTION_TYPE.DIVIDE_BY_ZERO,
                expression=self.expression,
                positions=list(range(*[check_tokens[0].range[0], check_tokens[2].range[1]])),
                computing_unit=check_tokens[0].value + check_tokens[1].value + check_tokens[2].value,
            )
        return check_tokens

    def _fractionalization(self) -> None:
        r"""
        将表达式Token流中的各种数字转换为分数
        :return: None
        """

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

            fraction = [Token(Token.TYPE.INTEGER,
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
                else:
                    base_number, repeat_part = process_decimal.split(':')

                    if '.' in base_number:
                        integer_part, decimal_part = base_number.split('.')
                        finite_part = integer_part + "." + decimal_part
                    else:
                        # 如果基数部分没有小数点，加上.0
                        finite_part = base_number + ".0"

                    return [repeat_part, finite_part]

            def _fraction_from_parts(repeat_part: str, finite_part: str) -> list[Token, Token, Token]:
                r"""
                根据循环部分和有限部分计算分数形式
                :param repeat_part: 循环部分
                :param finite_part: 有限部分
                :return: 转换后的分数Token流(分子,分数线,分母)
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
                fraction = [Token(Token.TYPE.INTEGER,
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
                return fraction

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
                percentage_str = integer_part[:decimal_point_pos] + '.' + integer_part[decimal_point_pos:] + decimal_part

            percentage_str = percentage_str.rstrip('0')
            if percentage_str.endswith('.'):
                percentage_str = percentage_str[:-1]

            return [Token(Token.TYPE.INTEGER, percentage_str, [percentage.range[0], percentage.range[0] + len(percentage_str)]),
                    Token(Token.TYPE.OPERATOR, "/", [percentage.range[0] + len(percentage_str), percentage.range[0] + len(percentage_str) + 1]),
                    Token(Token.TYPE.INTEGER, "1",
                          [percentage.range[0] + len(percentage_str) + 1, percentage.range[0] + len(percentage_str) + 2]),
                    ] if '.' not in percentage_str else _convert_finite_decimal(Token(Token.TYPE.FINITE_DECIMAL, percentage_str, [percentage.range[0], percentage.range[0] + len(percentage_str)]))

        fractionalized_tokens = []

        convert_num_types = [
            Token.TYPE.PERCENTAGE,
            Token.TYPE.FINITE_DECIMAL,
            Token.TYPE.INFINITE_DECIMAL,
        ]

        tokens_to_fractionalized: list[Token] = []
        index = 0
        while index < len(self.tokens):
            temp_token = self.tokens[index]
            if (convert_type := temp_token.type) == Token.TYPE.INTEGER and \
                    index + 2 < len(self.tokens) and \
                    self.tokens[index + 1].value == "/" and \
                    self.tokens[index + 2].type == Token.TYPE.INTEGER:
                fractionalized_tokens += Evaluator.simplify(
                    self._check_denominator([temp_token, self.tokens[index + 1], self.tokens[index + 2]]))
                index += 3
            elif convert_type in convert_num_types:
                match convert_type:
                    case Token.TYPE.FINITE_DECIMAL:
                        tokens_to_fractionalized = self._check_denominator(_convert_finite_decimal(temp_token))
                    case Token.TYPE.INFINITE_DECIMAL:
                        tokens_to_fractionalized = self._check_denominator(_convert_infinite_decimal(temp_token))
                    case Token.TYPE.PERCENTAGE:
                        tokens_to_fractionalized = self._check_denominator(_convert_percentage(temp_token))
                fractionalized_tokens += Evaluator.simplify(tokens_to_fractionalized)
            else:
                fractionalized_tokens += [temp_token]
            index += 1

        self.tokens = fractionalized_tokens
        self.tokens, self.expression = Lexer.update(self.tokens)

    def _bracket_checking_harmonisation(self) -> None:
        """
        括号检查与统一化
        :raise OlocInvalidBracketException: 如果括号出现层级错误或不匹配
        :return: None
        """
        # 定义括号的层级优先级
        BRACKET_PRIORITY = {'(': 1, '[': 2, '{': 3, ')': 1, ']': 2, '}': 3}
        # 定义括号的左右匹配关系
        BRACKET_MATCH = {'(': ')', '[': ']', '{': '}', ')': '(', ']': '[', '}': '{'}

        # 栈结构用于匹配括号
        stack = []

        for temp_token in self.tokens:
            if temp_token.type == Token.TYPE.LBRACKET:  # 左括号
                # 检查层级是否合法
                if stack and BRACKET_PRIORITY[temp_token.value] > BRACKET_PRIORITY[stack[-1][0]]:
                    raise OlocInvalidBracketException(
                        exception_type=OlocInvalidBracketException.EXCEPTION_TYPE.INCORRECT_BRACKET_HIERARCHY,
                        expression=self.expression,
                        positions=[temp_token.range[0]],
                        err_bracket=temp_token.value
                    )

                # 将左括号压入栈 (括号值, 起始位置, 优先级)
                stack.append((temp_token.value, temp_token.range[0], BRACKET_PRIORITY[temp_token.value]))

            elif temp_token.type == Token.TYPE.RBRACKET:  # 右括号
                # 栈为空时，左括号缺失
                if not stack:
                    raise OlocInvalidBracketException(
                        exception_type=OlocInvalidBracketException.EXCEPTION_TYPE.MISMATCH_RIGHT_BRACKET,
                        expression=self.expression,
                        positions=[temp_token.range[0]],
                        err_bracket=temp_token.value
                    )

                # 弹出栈顶元素
                last_left_bracket, last_position, last_priority = stack.pop()

                # 检查括号是否匹配
                if BRACKET_MATCH[last_left_bracket] != temp_token.value:
                    raise OlocInvalidBracketException(
                        exception_type=OlocInvalidBracketException.EXCEPTION_TYPE.MISMATCH_LEFT_BRACKET,
                        expression=self.expression,
                        positions=[last_position],
                        err_bracket=last_left_bracket
                    )

                # 检查层级是否合法
                if BRACKET_PRIORITY[last_left_bracket] != BRACKET_PRIORITY[temp_token.value]:
                    raise OlocInvalidBracketException(
                        exception_type=OlocInvalidBracketException.EXCEPTION_TYPE.INCORRECT_BRACKET_HIERARCHY,
                        expression=self.expression,
                        positions=[last_position],
                        err_bracket=last_left_bracket
                    )

        # 检查是否有未匹配的左括号
        if stack:
            last_left_bracket, last_position, _ = stack.pop()
            raise OlocInvalidBracketException(
                exception_type=OlocInvalidBracketException.EXCEPTION_TYPE.MISMATCH_LEFT_BRACKET,
                expression=self.expression,
                positions=[last_position],
                err_bracket=last_left_bracket
            )

        for bracket_token in self.tokens:
            if bracket_token.type == Token.TYPE.LBRACKET:
                bracket_token.value = '('
            elif bracket_token.type == Token.TYPE.RBRACKET:
                bracket_token.value = ')'

        Lexer.update(self.tokens)

    def _function_conversion(self) -> None:
        r"""
        根据函数转换表，将表达式中的右侧形式替换为左侧标准形式
        :return: None
        """

        function_conversion_table = utils.get_function_conversion_table()

        class Expression:
            r"""
            表达式子单元
            :param tokens_to_build: 构造该表达式部分的子单元
            """

            def __init__(self, tokens_to_build: list[Token]):
                self.tokens = tokens_to_build

            def __repr__(self):
                return f"Expression: {self.tokens}"

        def _build_match(match_case: str) -> list[Token | Expression]:
            r"""
            根据需要匹配的字符串形式构造对应匹配模式的列表
            :param match_case: 需要匹配的字符串形式的模式
            :return: 一个列表,对应需要匹配的模式
            """
            match = Lexer.tokenizer(match_case)
            result = []
            for temp_token in match:
                if temp_token.type == Token.TYPE.LONG_CUSTOM and temp_token.value in ['<__reserved_param1__>', '<__reserved_param2__>']:
                    result.append(Expression([temp_token]))
                else:
                    result.append(temp_token)
            return result

        def _find_match(match_case: list[Token | Expression], token_list: list[Token | Expression]) -> list[bool, list[int, int]]:
            r"""
            找到Token流中和匹配模式匹配的部分
            :param match_case: 需要匹配的流形式
            :param token_list: 待匹配的模式流
            :return: 一个列表.第一项是是否匹配到结果,第二项是两个元素的整数列表,对应范围的下标.
            """
            def _is_match(units_of_list: list[Token | Expression], units_of_match: list[Token | Expression]) -> bool:
                r"""
                判断对应单元是否匹配
                :param units_of_list: 待匹配流中的单元块(列表)
                :param units_of_match: 模式流中的单元块(列表)
                :return: 是否匹配
                """
                for list_unit, match_unit in zip(units_of_list, units_of_match):
                    if isinstance(list_unit, Expression) and isinstance(match_unit, Expression):
                        continue
                    if isinstance(list_unit, Token) and isinstance(match_unit, Token) and list_unit.type == match_unit.type:
                        # 自定义短/长无理数: 不需要内容一致
                        if list_unit.type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM] and match_unit.type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM]:
                            continue
                    if not list_unit.value == match_unit.value:
                        break
                else:
                    return True
                return False

            for index, unit in enumerate(token_list):
                if unit == match_case[0] and (attempt_length := index + len(match_case)) <= len(token_list):
                    if _is_match(token_list[index:attempt_length], match_case):
                        return [True, [index, attempt_length]]
            return [False, [0, 0]]

        def _convert_match(to_convert: list[Token | Expression], match_pattern: list[Token | Expression], match_range: [int, int]) -> list[Token]:
            r"""
            将找到的匹配结构转换为convert_to的结构, 并解开Expression
            :param to_convert: 待修改的Token | Expression流
            :param match_pattern: 匹配的Token | Expression流
            :param match_range: 被匹配的模式范围
            :return:
            """
            def _unwrap_to_token_list(process_list: list[Token | Expression]) -> list[Token]:
                r"""
                将Token | Expression流转换为Token流
                :param process_list: 待转换的Token | Expression流
                :return: 转换后的Token流
                """
                unwrap_result = []
                for process_unit in process_list:
                    if isinstance(process_unit, Expression):
                        unwrap_result.extend(process_unit.tokens)
                    else:
                        unwrap_result.append(process_unit)
                return unwrap_result

            result = to_convert[:match_range[0]]

            params = [unit for unit in to_convert[match_range[0]:match_range[1]] if isinstance(unit, Expression)]

            param_index = 0
            after_convert = []
            for temp_unit in match_pattern:
                if isinstance(temp_unit, Expression):
                    after_convert.append(params[param_index])
                    param_index += 1
                after_convert.append(temp_unit)

            result += after_convert + to_convert[match_range[1]:]

            return _unwrap_to_token_list(result)

        def _has_convert(token_list: list[Token], matches_to_judge: list[list[Token]]) -> bool:
            r"""
            判断Token流中是否存在可转换的结构
            :param token_list: 待转换的结构
            :param matches_to_judge: 待判断的缓存匹配
            :return: 是否存在
            """
            for temp_match in matches_to_judge:
                if _find_match(temp_match, token_list):
                    return True
            return False

        def _build_expression_token_list(token_list: list[Token]) -> list[Token | Expression]:
            r"""
            将Token流中表达式部分转换为Expression
            :param token_list: 待转换的Token流
            :return: 转换后的Token | Expression流. 如果输入和输出一致,说明不再有可以转换的部分了.
            """
            for function_strs in utils.get_function_conversion_table().values():
                for function_str in function_strs:
                    ...
            return token_list

        matches = []
        for key, value_list in function_conversion_table.items():
            for value in value_list:
                matches.append(_build_match(value))

        while True:
            expression_list = _build_expression_token_list(self.tokens)
            for match_case in matches:
                is_find, find_range = _find_match(match_case, expression_list)
                if is_find:
                    self.tokens = _convert_match(expression_list, match_case, find_range)
                    Lexer.update(self.tokens)
            if not _has_convert(self.tokens, matches):
                break

    def _static_check(self) -> None:
        r"""
        对表达式执行静态检查
        :return: None
        """

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
        self._function_conversion()
        self.time_cost = time.time_ns() - start_time

    """
    静态方法
    """

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :raise OlocIrrationalNumberException: 如果无理数形式不合法
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

    @staticmethod
    def update(tokens: list[Token]) -> [list[Token], str]:
        r"""
        更新输入的Token流
        :return: 一个列表,第一项是更新后的Token流,第二项是表达式字符串
        """
        # 清空表达式和起始下标
        expression = ""
        start_index = 0

        # 遍历所有Token，拼接表达式并检查下标连续性
        for index, process_token in enumerate(tokens):
            # 拼接表达式
            expression += process_token.value

            # 如果是第一个Token，直接设置其下标
            if index == 0:
                process_token.range = [start_index, start_index + len(process_token.value)]
                start_index = process_token.range[1]
                continue

            # 检查当前Token和前一个Token的下标连续性
            previous_token = tokens[index - 1]
            if previous_token.range[1] != process_token.range[0]:
                # 下标不连续，重新分配当前Token及后续Token的下标
                process_token.range = [start_index, start_index + len(process_token.value)]
            else:
                # 下标连续，保持当前下标
                process_token.range = [previous_token.range[1], previous_token.range[1] + len(process_token.value)]

            # 更新起始下标
            start_index = process_token.range[1]
        return [tokens, expression]


"""test"""
if __name__ == '__main__':
    import oloc_preprocessor as preprocessor

    import simpsave as ss

    tests = ss.read("test_cases", file="./data/olocconfig.ini")
    # input(f"{len(tests)}>>>")
    start = time.time()
    for test in tests:
        try:
            preprocess = preprocessor.Preprocessor(test)
            preprocess.execute()
            #print(test, end=" => ")
            lexer = Lexer(preprocess.expression)
            lexer.execute()
            for token in lexer.tokens:
                ... # debug
                #print(token.value, end=" ")
            #print(f"\t {preprocess.time_cost / 1000000} ms {lexer.time_cost / 1000000} ms")
        except (TypeError, ZeroDivisionError) as t_error:
            raise t_error
        except Exception as error:
            print(f"\n\n\n========\n\n{error}\n\n\n")
    print(f"Run {len(tests)} in {time.time() - start}")

    while True:
        try:
            preprocess = preprocessor.Preprocessor(input(">>>"))
            preprocess.execute()
            lexer = Lexer(preprocess.expression)
            lexer.execute()
            print(lexer.tokens)
            for token in lexer.tokens:
                print(token.value, end=" ")
            print(f"\nIn {preprocess.time_cost / 1000000000} + {lexer.time_cost / 1000000000} = {preprocess.time_cost + lexer.time_cost} s")
        except (TypeError, ZeroDivisionError) as t_error:
            raise t_error
        except Exception as error:
            print(error)

    preprocess = preprocessor.Preprocessor(input(">>>"))
    preprocess.execute()
    lexer = Lexer(preprocess.expression)
    lexer.execute()
    print(lexer.tokens)
    for token in lexer.tokens:
        print(token.value, end=" ")
r"""
:author: WaterRun
:date: 2025-03-09
:file: preprocessor.py
:description: Oloc preprocessor
"""

import re
import utils

from source.oloc.exceptions import *


class Preprocessor:
    r"""
    预处理器
    :param expression: 待处理的表达式
    """

    expression: str = ''

    def __init__(self, expression: str):
        self.expression = expression

    def _remove_comment(self) -> None:
        r"""
        移除表达式中的@结尾注释和##包裹的自由注释
        :return: None
        :raise OlocFreeCommentException: 如果出现无法匹配的#
        """

        # 移除结尾注释
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # 检查自由注释的匹配情况
        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        if len(hash_positions) % 2 != 0:
            unmatched_position = [hash_positions[-1]]
            raise OlocFreeCommentException(
                exception_type=OlocFreeCommentException.ExceptionType.MISMATCH,
                expression=self.expression,
                positions=unmatched_position
            )

        pattern = r'#(.*?)#'
        self.expression = re.sub(pattern, '', self.expression).strip()

    def _symbol_mapper(self) -> None:
        r"""
        读取符号映射表,并依次遍历进行映射;对于函数名称中的符号,不进行替换处理
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()
        function_name_list = utils.get_function_name_list()

        function_name_set = set(function_name_list)

        expression_chars = list(self.expression)
        length = len(expression_chars)

        for target, sources in symbol_mapping_table.items():
            for source in sources:
                index = 0
                while index <= length - len(source):  # 确保不越界
                    if ''.join(expression_chars[index:index + len(source)]) == source:
                        is_function_part = False
                        for func in function_name_set:
                            if ''.join(expression_chars[index:index + len(func)]) == func:
                                is_function_part = True
                                break

                        if not is_function_part:
                            expression_chars[index:index + len(source)] = list(target)
                            length = len(expression_chars)
                            index += len(target)
                        else:
                            index += len(source)
                    else:
                        index += 1

        self.expression = ''.join(expression_chars)

    def _formal_elimination(self) -> None:
        r"""
        消除表达式中的一些特殊形式.包括数字分隔符,括号化简,正负号消除
        :return: None
        :raise OlocNumberSeparatorException: 检测到数字分隔符不合法
        """

        def _simplify_signs(expression):
            r"""
            对表达式中的连续正负号进行约简

            :param expression: 待约简的表达式
            :return: 约简后的表达式
            """

            r"""
            转化原则:
            ++ -> +
            -- -> +
            +- -> -
            -+ -> -
            """

            result = []
            index = 0
            while index < len(expression):
                if expression[index] in '+-':
                    # 收集连续的符号
                    sign_sequence = []
                    while index < len(expression) and expression[index] in '+-':
                        sign_sequence.append(expression[index])
                        index += 1

                    # 计算净符号，根据奇偶性决定最终符号
                    if sign_sequence.count('-') % 2 == 0:  # 偶数个负号
                        result.append('+')
                    else:  # 奇数个负号
                        result.append('-')
                else:
                    # 非符号字符直接加入结果
                    result.append(expression[index])
                    index += 1

            return ''.join(result)

        def _remove_numeric_separators(expression):
            r"""
            移除表达式中的数字分隔符`,`，并验证分隔符规则。
            :param expression: 输入的数学表达式
            :return: 返回移除分隔符后的表达式
            :raise OlocNumberSeparatorException: 如果出现分隔符规则被违反的情况
            """

            invalid_separator_positions = []
            for match in re.finditer(r',', expression):
                index = match.start()

                # 判断逗号是否是有效的数字分隔符 (例如: 1,234)
                is_valid_numeric_separator = (
                        0 < index < len(expression) - 1 and  # 逗号不在开头或结尾
                        expression[index - 1].isdigit() and  # 逗号前是数字
                        expression[index + 1].isdigit()  # 逗号后是数字
                )

                # 判断逗号是否是连续分隔符错误 (例如: 1,,234)
                is_invalid_consecutive_comma = (
                        0 < index < len(expression) - 1 and  # 逗号不在开头或结尾
                        expression[index - 1] != ',' and  # 逗号前不是逗号
                        expression[index + 1] == ','  # 逗号后是逗号
                )

                # 如果逗号既不是有效分隔符，也不是连续分隔符错误，记录其位置
                if not is_valid_numeric_separator and not is_invalid_consecutive_comma:
                    invalid_separator_positions.append(index)

            if invalid_separator_positions:
                raise OlocNumberSeparatorException(
                    OlocNumberSeparatorException.ExceptionType.INVALID_SEPARATOR,
                    expression,
                    invalid_separator_positions
                )

            sanitized_expression = expression.replace(",", "")
            return sanitized_expression

        # 正负号消除
        self.expression = _simplify_signs(self.expression)

        # 数字分隔符消除
        self.expression = _remove_numeric_separators(self.expression)

    def _formal_completion(self):
        r"""
        补全表达式中的一些可省略的特殊形式.包括隐式的乘法符号
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()
        reserved_symbols = set(symbol_mapping_table.keys())

        left_brackets = '([{'
        right_brackets = ')]}'

        result = []
        in_custom_irrational = False

        i = 0
        while i < len(self.expression):
            current_char = self.expression[i]

            if current_char == '<':
                in_custom_irrational = True
            elif current_char == '>':
                in_custom_irrational = False

            result.append(current_char)

            if i < len(self.expression) - 1:
                next_char = self.expression[i + 1]

                if not in_custom_irrational:
                    is_current_short_irrational = current_char.isalpha() and current_char not in reserved_symbols
                    is_current_irrational = is_current_short_irrational or current_char in "π𝑒"
                    is_next_short_irrational = next_char.isalpha() and next_char not in reserved_symbols
                    is_next_irrational = is_next_short_irrational or next_char in "π𝑒"

                    # 直接处理问号后面跟着字母、数字或左括号的情况
                    if current_char == '?' and (next_char.isalnum() or next_char in left_brackets or next_char == '<'):
                        result.append('*')
                    else:
                        # 应用正常的隐式乘法规则
                        if current_char.isdigit() and next_char in left_brackets:
                            result.append('*')
                        elif current_char in right_brackets and (
                                next_char.isdigit() or is_next_irrational or next_char == '<' or next_char in left_brackets):
                            result.append('*')
                        elif current_char.isdigit() and (is_next_irrational or next_char == '<'):
                            result.append('*')
                        elif (is_current_irrational or current_char == '>') and next_char.isdigit():
                            result.append('*')
                        elif current_char in right_brackets and (is_next_irrational or next_char == '<'):
                            result.append('*')
                        elif (is_current_irrational or current_char == '>') and next_char in left_brackets:
                            result.append('*')
                        elif (is_current_irrational or current_char == '>') and (
                                is_next_irrational or next_char == '<'):
                            result.append('*')

            i += 1

        self.expression = ''.join(result)

    def _convert_fraction(self):
        r"""
        将表达式中的各种有理数进行分数化
        :return: None
        """

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()
        self._formal_elimination()
        self._formal_completion()


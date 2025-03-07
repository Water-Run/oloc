r"""
:author: WaterRun
:date: 2025-03-08
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
                # 合法：逗号前后必须是数字
                if not (index > 0 and index < len(expression) - 1 and expression[index - 1].isdigit() and expression[
                    index + 1].isdigit()):
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


    def _convert_fraction(self):
        r"""
        将表达式中的各种有理数进行分数化
        :return: None
        """

        def _eliminate_digit_separator(expression: str) -> str:
            r"""
            消除数字分隔符
            :param expression:
            :return:
            """

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()
        self._formal_elimination()


"""test"""
while True:
    try:
        process = Preprocessor(input('>>'))
        process.execute()
        print(process.expression)
    except OlocException as error:
        print(error)

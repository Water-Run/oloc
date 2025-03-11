r"""
:author: WaterRun
:date: 2025-03-11
:file: preprocessor.py
:description: Oloc preprocessor
"""

from source.oloc.exceptions import *
from source.oloc.lexer import *


class Preprocessor:
    r"""
    预处理器
    :param: expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression

    def _remove_comment(self) -> None:
        r"""
        移除表达式中的@结尾注释和##包裹的自由注释
        :return: None
        :raise OlocCommentException: 如果出现无法匹配的#
        """

        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        if len(hash_positions) % 2 != 0:
            unmatched_position = [hash_positions[-1]]
            raise OlocCommentException(
                exception_type=OlocCommentException.ExceptionType.MISMATCH_HASH,
                expression=self.expression,
                positions=unmatched_position
            )

        pattern = r'#(.*?)#'
        self.expression = re.sub(pattern, '', self.expression).strip()

    def _symbol_mapper(self) -> None:
        r"""
        读取符号映射表,并依次遍历进行映射;对于函数名称中的符号,以及自定义长无理数中的符号,不进行替换处理
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()
        function_name_list = utils.get_function_name_list()

        # 创建反向映射表：将值映射到键
        reverse_mapping = {}
        for key, values in symbol_mapping_table.items():
            for value in values:
                reverse_mapping[value] = key

        def replace_symbols(text: str) -> str:
            # 找到 "<" 和 ">" 的范围，并记录这些区域
            angle_bracket_ranges = []
            inside_angle_brackets = False
            start_index = 0
            for i, char in enumerate(text):
                if char == "<":
                    inside_angle_brackets = True
                    start_index = i
                elif char == ">" and inside_angle_brackets:
                    inside_angle_brackets = False
                    angle_bracket_ranges.append((start_index, i))

            # 遍历符号映射表，进行替换，但跳过 "<...>" 和函数名
            replaced_text = []
            i = 0
            while i < len(text):
                # 检查当前字符是否在 "<...>" 范围内
                if any(start <= i <= end for start, end in angle_bracket_ranges):
                    replaced_text.append(text[i])
                    i += 1
                    continue

                # 检查是否匹配函数名（完整匹配）
                is_function_name = False
                for func_name in function_name_list:
                    if text[i:i + len(func_name)] == func_name and (
                            i + len(func_name) == len(text) or not text[i + len(func_name)].isalnum()
                    ):
                        replaced_text.append(func_name)
                        i += len(func_name)
                        is_function_name = True
                        break
                if is_function_name:
                    continue

                # 检查是否匹配符号映射表
                matched = False
                for value, key in reverse_mapping.items():
                    if text[i:i + len(value)] == value:
                        replaced_text.append(key)
                        i += len(value)
                        matched = True
                        break
                if not matched:
                    replaced_text.append(text[i])
                    i += 1

            return "".join(replaced_text)

        # 替换 self.expression
        self.expression = replace_symbols(self.expression)

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

                is_valid_numeric_separator = (
                        0 < index < len(expression) - 1 and  # 逗号不在开头或结尾
                        expression[index - 1].isdigit() and  # 逗号前是数字
                        expression[index + 1].isdigit()  # 逗号后是数字
                )

                is_invalid_consecutive_comma = (
                        0 < index < len(expression) - 1 and  # 逗号不在开头或结尾
                        expression[index - 1] != ',' and  # 逗号前不是逗号
                        expression[index + 1] == ','  # 逗号后是逗号
                )

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

        self.expression = _simplify_signs(self.expression)

        self.expression = _remove_numeric_separators(self.expression)

    def _formal_completion(self):
        r"""
        补全表达式中的一些可省略的特殊形式.包括隐式的乘法符号
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()
        function_names = utils.get_function_name_list()
        protect = []
        for func in function_names:
            start = 0
            while True:
                index = self.expression.find(func, start)
                if index == -1:
                    break
                protect.extend(range(index, index + len(func)))
                start = index + len(func)

        reserved_symbols = set(symbol_mapping_table.keys())

        left_brackets = '([{'
        right_brackets = ')]}'

        result = []
        in_custom_irrational = False

        index = 0
        while index < len(self.expression):
            current_char = self.expression[index]

            if index in protect:
                result.append(current_char)
                index += 1
                continue

            if current_char == '<':
                in_custom_irrational = True
            elif current_char == '>':
                in_custom_irrational = False

            result.append(current_char)

            if index < len(self.expression) - 1:
                next_char = self.expression[index + 1]

                if not in_custom_irrational:
                    is_current_short_irrational = current_char.isalpha() and current_char not in reserved_symbols
                    is_current_irrational = is_current_short_irrational or current_char in "π𝑒"
                    is_next_short_irrational = next_char.isalpha() and next_char not in reserved_symbols
                    is_next_irrational = is_next_short_irrational or next_char in "π𝑒"

                    if current_char == '?' and (next_char.isalnum() or next_char in left_brackets or next_char == '<'):
                        result.append('*')
                    else:
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

            index += 1

        self.expression = ''.join(result)

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()
        self._formal_elimination()
        self._formal_completion()


"""test"""
if __name__ == '__main__':
    import simpsave as ss
    import time
    start = time.time()
    count = 0
    test_cases = ss.read("test_cases", file="./data/olocconfig.ini")
    for test in test_cases:
        try:
            result = Preprocessor(test)
            result.execute()
            print(f"{test}\t=>\t{result.expression}")
        except Exception as error:
            print("\n\n\n============\n", end="Expression: ")
            print(test)
            print(error)
            print("" * 3)
        count += 1
    print(f"Test {count} tests in {time.time() - start}" + "" * 10)

    while True:
        try:
            result = Preprocessor(input(">>"))
            result.execute()
            print(result.expression)
        except Exception as error:
            print(error)

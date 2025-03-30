r"""
:author: WaterRun
:date: 2025-03-30
:file: oloc_preprocessor.py
:description: Oloc preprocessor
"""

import time
import re

import oloc_utils as utils
from oloc_exceptions import *


class Preprocessor:
    r"""
    Preprocessor
    :param: expression: The expression to be processed
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.time_cost = -1
        self._symbol_mapping_table = utils.get_symbol_mapping_table()
        self._function_mapping_table = utils.get_function_mapping_table()
        self._function_name_list = utils.get_function_name_list()

    def _remove_comment(self) -> None:
        r"""
        Removes trailing comments ending with `@` and free comments enclosed with `##` in the expression.
        :return: None
        :raise OlocCommentException: If unmatched `#` occurs
        """

        # Remove trailing comments
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # Remove free comments
        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        if len(hash_positions) % 2 != 0:
            unmatched_position = [hash_positions[-1]]
            raise OlocCommentException(
                exception_type=OlocCommentException.EXCEPTION_TYPE.MISMATCH_HASH,
                expression=self.expression,
                positions=unmatched_position
            )

        pattern = r'#(.*?)#'
        self.expression = re.sub(pattern, '', self.expression).strip()

    def _normalize_superscript_symbols(self) -> None:
        r"""
        Converts superscript-style exponents in the expression into a uniform format.
        :return: None
        """
        superscripts = {'¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
                        '⁰': '0'}

        normalized = ""
        for superscript_index, char in enumerate(self.expression):
            if char in superscripts.keys():
                if superscript_index > 0 and self.expression[superscript_index - 1] in superscripts.keys():
                    normalized += superscripts[char]
                else:
                    normalized += "^" + superscripts[char]
            else:
                normalized += self.expression[superscript_index]
        self.expression = normalized

    def _mark_long_custom_index(self) -> list[tuple[int, int]]:
        r"""
        Marks the indices of custom long irrational numbers in the expression.
        :return: A list of marked indices
        """
        long_custom_start_stack = []
        custom_indices = []
        for exp_index, char in enumerate(self.expression):
            if char == '<':
                long_custom_start_stack.append(exp_index)
            if char == '>':
                if len(long_custom_start_stack) == 1:
                    custom_indices.append((long_custom_start_stack[0], exp_index))
                if len(long_custom_start_stack) == 0:
                    raise OlocIrrationalNumberFormatException(
                        exception_type=OlocIrrationalNumberFormatException.EXCEPTION_TYPE.MISMATCH_LONG_RIGHT_SIGN,
                        expression=char,
                        positions=[exp_index],
                    )
                long_custom_start_stack.pop()
        return custom_indices

    def _is_protected(self, target_index: int, protected_indices: list[tuple[int, int]]) -> bool:
        r"""
        Checks if a certain index is in the protected area.
        :param target_index: The target index
        :param protected_indices: A list of protected index ranges
        :return: Whether it is protected
        """
        for start, end in protected_indices:
            if start <= target_index < end:
                return True
        return False

    def _replace_symbols(self, mapping_table: dict, protected_indices: list[tuple[int, int]]) -> str:
        r"""
        Performs symbol mapping on the expression.
        :param mapping_table: A mapping table containing mappings for replacement
        :param protected_indices: A list of protected target_index ranges
        :return: The processed expression
        """
        result = []
        i = 0
        while i < len(self.expression):
            if self._is_protected(i, protected_indices):
                # If the current target_index is in a protected area, directly add the character
                result.append(self.expression[i])
                i += 1
            else:
                replaced = False
                # Traverse the mapping table and attempt replacement
                for key, values in mapping_table.items():
                    for value in values:
                        if self.expression.startswith(value, i):
                            result.append(key)
                            i += len(value)
                            replaced = True
                            break
                    if replaced:
                        break
                if not replaced:
                    # If not replaced, directly add the character
                    result.append(self.expression[i])
                    i += 1
        return ''.join(result)

    def _symbol_mapper(self) -> None:
        r"""
        Reads the symbol mapping table and maps symbols sequentially. Symbols in function names and custom long
        irrational numbers are not replaced.
        :return: None
        """
        symbol_mapping_table = self._symbol_mapping_table

        def _mark_function_index() -> list[tuple[int, int]]:
            r"""
            Marks the indices of functions in the expression.
            :return: A list of marked indices
            """
            function_names = self._function_name_list
            mark_function_indices = []
            for func in function_names:
                start = 0
                while (exp_index := self.expression.find(func, start)) != -1:
                    end = exp_index + len(func)
                    mark_function_indices.append((exp_index, end))
                    start = end
            return mark_function_indices

        # Mark protected areas
        function_indices = _mark_function_index()
        custom_indices = self._mark_long_custom_index()
        protected_indices = function_indices + custom_indices

        # Replace symbols
        self.expression = self._replace_symbols(symbol_mapping_table, protected_indices)

    def _function_mapper(self) -> None:
        r"""
        Reads the function mapping table and maps symbols sequentially. Symbols in custom long
        irrational numbers are not replaced.
        :return: None
        """
        function_mapping_table = self._function_mapping_table

        # Mark protected areas
        protected_indices = self._mark_long_custom_index()

        # Replace symbols
        self.expression = self._replace_symbols(function_mapping_table, protected_indices)

    def _equals_sign_elimination(self) -> None:
        r"""
        Eliminates trailing `=` in the expression.
        :raise OlocInvalidEqualSignException: If `=` appears in a non-trailing position
        :return: None
        """
        if self.expression.endswith('='):
            self.expression = self.expression[:-1]
        equal_sign_index = self.expression.find('=')
        if equal_sign_index != -1:
            raise OlocInvalidEqualSignException(
                exception_type=OlocInvalidEqualSignException.EXCEPTION_TYPE.MISPLACED,
                expression=self.expression,
                positions=[equal_sign_index],
            )

    def _formal_elimination(self) -> None:
        r"""
        消除表达式中冗余的正负号和数字分隔符。
        :return: None
        :raise OlocNumberSeparatorException: 如果数字分隔符中存在错误。
        :raise OlocFunctionParameterException: 如果出现在函数之外的函数分隔符
        """

        # 消除连续正负号
        def _simplify_signs(match: re.Match) -> str:
            r"""
            根据正负号消除原则，简化连续的正负号。

            :param match: 匹配到的符号序列（re.Match 对象）
            :return: 简化后的单个符号（'+' 或 '-'）。
            """
            sign_sequence = match.group()  # 获取匹配的符号序列
            return '-' if sign_sequence.count('-') % 2 == 1 else '+'

        # 消除表达式中的冗余正负号
        self.expression = re.sub(r'[+-]+', _simplify_signs, self.expression)

        # 去除开头多余的正号（如 "+a" -> "a"）
        if self.expression.startswith('+'):
            self.expression = self.expression[1:]

        # 获取函数名称列表
        function_names = self._function_name_list

        # 定义块类型枚举
        class BlockType(Enum):
            r"""
            子单元的类型字符串枚举
            """
            FUNCTION_WITH_COMMA = "FUNCTION_WITH_COMMA"
            FUNCTION_WITHOUT_COMMA = "FUNCTION_WITHOUT_COMMA"
            NORMAL = "NORMAL"

        def _has_semicolon(start_index: int) -> bool:
            r"""
            向后尝试判断函数参数是否以`;`作为分隔符。
            通过遍历表达式内容，找到当前函数参数的分隔符格式。

            :param start_index: 当前检查位。
            :return: 是否有`;`形式的函数分隔符。
            """
            bracket_count = 1
            for exp_index in range(start_index, len(self.expression)):
                exp_char = self.expression[exp_index]
                if exp_char == '(':
                    bracket_count += 1
                elif exp_char == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return False  # 找到匹配的右括号，未发现 `;` 分隔符
                elif exp_char == ';' and bracket_count == 1:
                    return True  # 在当前括号层发现 `;`
            return False

        # 初始化变量
        stack = []  # 用于跟踪嵌套块的类型
        invalid_positions = []  # 用于记录无效的数字分隔符位置
        result = []  # 最终结果的字符列表
        i = 0  # 当前字符索引

        # 主循环遍历表达式中的字符
        while i < len(self.expression):
            char = self.expression[i]

            # 检查是否是函数名的开始
            matched_function = next(
                (
                    fn for fn in function_names
                    if self.expression.startswith(fn, i) and i + len(fn) < len(self.expression) and \
                       self.expression[i + len(fn)] == '('
                ),
                None,
            )

            if matched_function:
                result.append(matched_function)
                i += len(matched_function)
                continue

            # 处理左括号
            if char == '(':
                # 检查是否为函数的左括号
                is_function_bracket = any(
                    self.expression.startswith(fn, i - len(fn))
                    for fn in function_names
                )

                if is_function_bracket:
                    if _has_semicolon(i + 1):
                        stack.append((BlockType.FUNCTION_WITHOUT_COMMA, len(stack)))
                    else:
                        stack.append((BlockType.FUNCTION_WITH_COMMA, len(stack)))
                else:
                    stack.append((BlockType.NORMAL, len(stack)))

                result.append(char)
                i += 1
                continue

            # 处理右括号
            if char == ')':
                if stack:
                    stack.pop()
                result.append(char)
                i += 1
                continue

            if char == ',':
                if stack and stack[-1][0] in {BlockType.FUNCTION_WITH_COMMA, BlockType.FUNCTION_WITHOUT_COMMA}:
                    if stack[-1][0] == BlockType.FUNCTION_WITH_COMMA:
                        result.append(char)
                else:
                    if (
                            i == 0 or i == len(self.expression) - 1 or
                            not self.expression[i - 1].isdigit() or
                            (i + 1 < len(self.expression) and not self.expression[i + 1].isdigit())
                    ):
                        invalid_positions.append(i)

                i += 1
                continue

            if char == ';':
                # 检查是否在函数内部
                if not (stack and stack[-1][0] in {BlockType.FUNCTION_WITH_COMMA, BlockType.FUNCTION_WITHOUT_COMMA}):
                    raise OlocFunctionParameterException(
                        exception_type=OlocFunctionParameterException.EXCEPTION_TYPE.OUTSIDE_SEPARATOR,
                        expression=self.expression,
                        positions=[i],
                        err_param=';',
                        err_info='Captured during preprocessing of digit delimiter conversions'
                    )
                i += 1
                continue

            # 其他字符直接添加到结果
            result.append(char)
            i += 1

        # 如果发现无效的数字分隔符，抛出异常
        if invalid_positions:
            raise OlocNumberSeparatorException(
                exception_type=OlocNumberSeparatorException.EXCEPTION_TYPE.INVALID_SEPARATOR,
                expression=self.expression,
                positions=invalid_positions,
            )

        # 更新表达式
        self.expression = ''.join(result)
        self.expression = self.expression.replace(";", ",")

    def execute(self) -> None:
        r"""
        Executes preprocessing and writes the result to `self.expression`.
        :return: None
        """

        start_time = time.time_ns()
        self._remove_comment()
        self._normalize_superscript_symbols()
        self._symbol_mapper()
        self._function_mapper()
        self._equals_sign_elimination()
        self._formal_elimination()
        self.time_cost = time.time_ns() - start_time

"""test"""

if __name__ == '__main__':
    import simpsave as ss

    tests = ss.read('test_cases', file='./data/oloctest.ini')
    time_costs = []
    print('___________')
    for index, test in enumerate(tests):
        if index % 200 == 0:
            print("=", end="")
        try:
            preprocessor = Preprocessor(test)
            preprocessor.execute()
            time_costs.append(preprocessor.time_cost)
        except:
            continue
    print(f"\n"
          f"Avg Time Cost For {len(time_costs)} cases: {sum(time_costs) / len(time_costs) / 1000000} ms\n"
          )

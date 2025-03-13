r"""
:author: WaterRun
:date: 2025-03-13
:file: preprocessor.py
:description: Oloc preprocessor
"""

from lexer import *


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

        # 移除结尾注释
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # 移除自由注释
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

    def _symbol_mapper(self) -> None:
        r"""
        读取符号映射表,并依次遍历进行映射;对于函数名称中的符号,以及自定义长无理数中的符号,不进行替换处理
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()

        def _replace_symbols(expression: str) -> str:
            r"""
            进行符号映射
            :param expression: 被处理的表达式
            :return: 处理后的表达式
            """

            def _mark_function_index() -> list[tuple[int, int]]:
                r"""
                标注表达式中的函数的下标
                :return: 标注后的下标列表
                """
                function_names = utils.get_function_name_list()
                function_indices = []
                for func in function_names:
                    start = 0
                    while (index := expression.find(func, start)) != -1:
                        end = index + len(func)
                        function_indices.append((index, end))
                        start = end
                return function_indices

            def _mark_long_custom_index() -> list[tuple[int, int]]:
                r"""
                标注表达式中的长自定义无理数下标
                :return: 标注后的下标列表
                """
                import re
                # 捕获自定义长无理数的完整范围
                pattern = r"<.*?>[+-]?\d*\.?\d*\?"
                custom_indices = []
                for match in re.finditer(pattern, expression):
                    custom_indices.append((match.start(), match.end()))
                return custom_indices

            def _is_protected(index: int) -> bool:
                r"""
                检查某个下标是否在保护区域
                :param index: 目标下标
                :return: 是否保护
                """
                for start, end in protected_indices:
                    if start <= index < end:
                        return True
                return False

            # 标记保护区域
            protected_indices = _mark_function_index() + _mark_long_custom_index()

            # 替换非保护部分
            result = []
            i = 0
            while i < len(expression):
                if _is_protected(i):
                    # 如果当前下标在保护区域，直接添加字符
                    result.append(expression[i])
                    i += 1
                else:
                    replaced = False
                    # 遍历符号映射表，尝试替换
                    for symbol, mappings in symbol_mapping_table.items():
                        for mapping in mappings:
                            if expression.startswith(mapping, i):
                                result.append(symbol)
                                i += len(mapping)
                                replaced = True
                                break
                        if replaced:
                            break
                    if not replaced:
                        # 如果未替换，直接添加字符
                        result.append(expression[i])
                        i += 1

            return ''.join(result)

        self.expression = _replace_symbols(self.expression)

    def _formal_elimination(self) -> None:
        r"""
        消除表达式中冗余的正负号和数字分隔符
        :return: None
        """

        r"""
        正负号消除原则
        ++ => +
        +- => -
        -+ => -
        -- => +
        """

        def _simplify(match):
            """
            根据正负号消除原则，简化连续的正负号。

            :param match: 正则表达式匹配到的 `Match` 对象，表示连续的正负号。
            :return: 简化后的单个符号（'+' 或 '-'）。
            """
            signs = match.group()  # 获取匹配到的连续正负号
            # 判断最终的符号是正还是负
            # 如果减号的数量是奇数，结果是负号，否则是正号
            return '-' if signs.count('-') % 2 == 1 else '+'

        # 匹配连续的 "+" 和 "-" 的部分，并进行替换
        self.expression = re.sub(r'[+-]+', _simplify, self.expression)

        # 去掉开头多余的正号（如 +a -> a）
        if self.expression.startswith('+'):
            self.expression = self.expression[1:]

        function_names = utils.get_function_name_list()
        symbol_mapping_table = utils.get_symbol_mapping_table()
        inside_function = False
        parentheses_stack = []
        invalid_positions = []
        remove_seperator_result_list = []
        i = 0

        while i < len(self.expression):
            char = self.expression[i]

            if not inside_function and any(
                self.expression[i:i+len(fn)] == fn for fn in function_names
            ):
                fn_length = next(len(fn) for fn in function_names if self.expression[i:i+len(fn)] == fn)
                if i + fn_length < len(self.expression) and self.expression[i + fn_length] == '(':
                    inside_function = True
                    parentheses_stack.append('(')
                    remove_seperator_result_list.append(self.expression[i:i + fn_length])
                    i += fn_length
                    continue

            if char == '(' and inside_function:
                parentheses_stack.append('(')
            elif char == ')' and inside_function:
                parentheses_stack.pop()
                if not parentheses_stack:
                    inside_function = False

            if char == ',':
                if inside_function:
                    remove_seperator_result_list.append(char)
                else:
                    if i == 0 or i == len(self.expression) - 1:
                        invalid_positions.append(i)
                    elif self.expression[i - 1] in [',', '.'] or self.expression[i + 1] in [',', '.']:
                        invalid_positions.append(i)
                    elif (not self.expression[i-1].isdigit() and self.expression[i - 1] in symbol_mapping_table.keys()) or (not self.expression[i+1].isdigit() and self.expression[i + 1] in symbol_mapping_table.keys()):
                        invalid_positions.append(i)
            else:
                remove_seperator_result_list.append(char)

            i += 1

        if invalid_positions:
            raise OlocNumberSeparatorException(
                exception_type=OlocNumberSeparatorException.EXCEPTION_TYPE['INVALID_SEPARATOR'],
                expression=self.expression,
                positions=invalid_positions
            )

        self.expression = ''.join(remove_seperator_result_list)

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()
        self._formal_elimination()


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
            print("\n\n\n\n\n============\n", end="Expression: ")
            print(test)
            print(error)
            print("\n" * 10)
        count += 1
    print(f"Test {count} tests in {time.time() - start}" + "" * 10)

    while True:
        try:
            result = Preprocessor(input(">>"))
            result.execute()
            print(result.expression)
        except Exception as error:
            print(error)

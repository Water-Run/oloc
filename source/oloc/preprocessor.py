r"""
:author: WaterRun
:date: 2025-03-12
:file: preprocessor.py
:description: Oloc preprocessor
"""

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

        # 移除结尾注释
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # 移除自由注释
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

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()


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

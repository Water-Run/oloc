r"""
:author: WaterRun
:date: 2025-03-17
:file: oloc_preprocessor.py
:description: Oloc preprocessor
"""

from oloc_lexer import *
import time


class Preprocessor:
    r"""
    Preprocessor
    :param: expression: The expression to be processed
    """

    def __init__(self, expression: str):
        self.expression = expression
        self.time_cost = -1

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
        for index, char in enumerate(self.expression):
            if char in superscripts.keys():
                if index > 0 and self.expression[index - 1] in superscripts.keys():
                    normalized += superscripts[char]
                else:
                    normalized += "^" + superscripts[char]
            else:
                normalized += self.expression[index]
        self.expression = normalized

    def _symbol_mapper(self) -> None:
        r"""
        Reads the symbol mapping table and maps symbols sequentially. Symbols in function names and custom long
        irrational numbers are not replaced.
        :return: None
        """
        symbol_mapping_table = utils.get_symbol_mapping_table()

        def _replace_symbols(expression: str) -> str:
            r"""
            Performs symbol mapping.
            :param expression: The expression to be processed
            :return: The processed expression
            """

            def _mark_function_index() -> list[tuple[int, int]]:
                r"""
                Marks the indices of functions in the expression.
                :return: A list of marked indices
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

            def _mark_long_custom_index() -> list[int, int]:
                r"""
                Marks the indices of custom long irrational numbers in the expression.
                :return: A list of marked indices
                """
                long_custom_start_stack = []
                custom_indices = []
                for index, char in enumerate(expression):
                    if char == '<':
                        long_custom_start_stack.append(index)
                    if char == '>':
                        if len(long_custom_start_stack) == 1:
                            custom_indices.append([long_custom_start_stack[0], index])
                        long_custom_start_stack.pop()
                return custom_indices

            def _is_protected(index: int) -> bool:
                r"""
                Checks if a certain index is in the protected area.
                :param index: The target index
                :return: Whether it is protected
                """
                for start, end in protected_indices:
                    if start <= index < end:
                        return True
                return False

            # Mark protected areas
            protected_indices = _mark_function_index() + _mark_long_custom_index()

            # Replace non-protected parts
            result = []
            i = 0
            while i < len(expression):
                if _is_protected(i):
                    # If the current index is in a protected area, directly add the character
                    result.append(expression[i])
                    i += 1
                else:
                    replaced = False
                    # Traverse the symbol mapping table and attempt replacement
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
                        # If not replaced, directly add the character
                        result.append(expression[i])
                        i += 1

            return ''.join(result)

        self.expression = _replace_symbols(self.expression)

    def _equals_sign_elimination(self) -> None:
        r"""
        Eliminates trailing `=` in the expression.
        :raise OlocInvalidEqualSignException: If `=` appears in a non-trailing position
        :return: None
        """
        if self.expression.endswith('='):
            self.expression = self.expression[:-1]
        index = self.expression.find('=')
        if index != -1:
            raise OlocInvalidEqualSignException(
                exception_type=OlocInvalidEqualSignException.EXCEPTION_TYPE.MISPLACED,
                expression=self.expression,
                positions=[index],
            )

    def _formal_elimination(self) -> None:
        r"""
        Eliminates redundant signs and number separators in the expression.
        :return: None
        :raise OlocNumberSeparatorException: If there are errors in the number separators
        """

        r"""
        Rules for eliminating redundant signs:
        ++ => +
        +- => -
        -+ => -
        -- => +
        """

        def _simplify(match):
            """
            Simplifies consecutive signs based on the rules for eliminating redundant signs.

            :param match: A `Match` object representing consecutive signs matched by the regular expression.
            :return: A single simplified sign ('+' or '-').
            """
            signs = match.group()  # Get the matched consecutive signs
            # Determine the resulting sign based on the count of '-' signs
            return '-' if signs.count('-') % 2 == 1 else '+'

        # Match consecutive "+" and "-" signs and replace them
        self.expression = re.sub(r'[+-]+', _simplify, self.expression)

        # Remove redundant leading "+" (e.g., +a -> a)
        if self.expression.startswith('+'):
            self.expression = self.expression[1:]

        function_names = utils.get_function_name_list()
        symbol_mapping_table = utils.get_symbol_mapping_table()

        # Use a stack to track brackets and function nesting
        # Stack element format: [type, level, function name (if it's a function)]
        # Type: 'F' for direct function parameter level, 'E' for expression level
        stack = []
        invalid_positions = []
        result = []

        i = 0
        while i < len(self.expression):
            char = self.expression[i]

            # Check if it is the start of a function name
            is_function_start = False
            matched_fn = None
            for fn in function_names:
                if (i + len(fn) <= len(self.expression) and
                        self.expression[i:i + len(fn)] == fn and
                        i + len(fn) < len(self.expression) and
                        self.expression[i + len(fn)] == '('):
                    is_function_start = True
                    matched_fn = fn
                    break

            if is_function_start:
                result.append(matched_fn)
                # Skip the function name
                i += len(matched_fn)
                continue

            # Handle commas
            if char == ',':

                if i == 0 or i == len(self.expression) - 1:
                    invalid_positions.append(i)
                elif not self.expression[i - 1].isdigit():
                    invalid_positions.append(i)
                elif i + 1 < len(self.expression) and not self.expression[i + 1].isdigit():
                    invalid_positions.append(i)
                # Valid number separator, do not add to the result (i.e., remove it)

                i += 1
                continue

            # Add other characters directly
            result.append(char)
            i += 1

        if invalid_positions:
            raise OlocNumberSeparatorException(
                exception_type=OlocNumberSeparatorException.EXCEPTION_TYPE.INVALID_SEPARATOR,
                expression=self.expression,
                positions=invalid_positions
            )

        self.expression = ''.join(result)
        self.expression = self.expression.replace(";", ",")  # Standardize function parameter format

    def execute(self) -> None:
        r"""
        Executes preprocessing and writes the result to `self.expression`.
        :return: None
        """

        start_time = time.time_ns()
        self._remove_comment()
        self._normalize_superscript_symbols()
        self._symbol_mapper()
        self._equals_sign_elimination()
        self._formal_elimination()
        self.time_cost = time.time_ns() - start_time

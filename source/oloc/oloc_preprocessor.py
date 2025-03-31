r"""
:author: WaterRun
:date: 2025-03-31
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
        :raise OlocSyntaxError: If unmatched `#` occurs
        """

        # Remove trailing comments
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # Remove free comments
        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        if len(hash_positions) % 2 != 0:
            unmatched_position = [hash_positions[-1]]
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.COMMENT_MISMATCH,
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
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.IRRATIONAL_RIGHT_BRACKET_MISMATCH,
                        expression=char,
                        positions=[exp_index],
                    )
                long_custom_start_stack.pop()
        return custom_indices

    def _replace_symbols(self, mapping_table: dict, protected_indices: list[tuple[int, int]]) -> str:
        r"""
        Performs symbol mapping on the expression.
        :param mapping_table: A mapping table containing mappings for replacement
        :param protected_indices: A list of protected target_index ranges
        :return: The processed expression
        """

        def _is_protected(target_index: int, indices: list[tuple[int, int]]) -> bool:
            r"""
            Checks if a certain index is in the protected area.
            :param target_index: The target index
            :param indices: A list of protected index ranges
            :return: Whether it is protected
            """
            for start, end in indices:
                if start <= target_index < end:
                    return True
            return False

        result = []
        index = 0
        while index < len(self.expression):
            if _is_protected(index, protected_indices):
                # If the current target_index is in a protected area, directly add the character
                result.append(self.expression[index])
                index += 1
            else:
                replaced = False
                # Traverse the mapping table and attempt replacement
                for key, values in mapping_table.items():
                    for value in values:
                        if self.expression.startswith(value, index):
                            result.append(key)
                            index += len(value)
                            replaced = True
                            break
                    if replaced:
                        break
                if not replaced:
                    # If not replaced, directly add the character
                    result.append(self.expression[index])
                    index += 1
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
        :raise OlocSyntaxError: If `=` appears in a non-trailing position
        :return: None
        """
        if self.expression.endswith('='):
            self.expression = self.expression[:-1]
        equal_sign_index = self.expression.find('=')
        if equal_sign_index != -1:
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.EQUAL_SIGN_MISPLACEMENT,
                expression=self.expression,
                positions=[equal_sign_index],
            )

    def _formal_elimination(self) -> None:
        r"""
        Eliminates redundant signs and numeric separators in the expression.
        :return: None
        :raise OlocSyntaxError: If there is an error in numeric separators.
        :raise OlocSyntaxError: If function delimiters appear outside the function scope.
        """

        # Eliminate consecutive signs
        def _simplify_signs(match: re.Match) -> str:
            r"""
            Simplifies consecutive signs based on sign elimination rules.
            :param match: Matched sequence of signs (re.Match object)
            :return: Simplified single sign ('+' or '-').
            """
            sign_sequence = match.group()  # Get the matched sequence of signs
            return '-' if sign_sequence.count('-') % 2 == 1 else '+'

        # Eliminate redundant signs in the expression
        self.expression = re.sub(r'[+-]+', _simplify_signs, self.expression)

        # Remove redundant '+' at the start (e.g., "+a" -> "a")
        if self.expression.startswith('+'):
            self.expression = self.expression[1:]

        # Get the list of function names
        function_names = self._function_name_list

        # Define an enumeration for block types
        class BlockType(Enum):
            r"""
            Enumeration of block type strings.
            """
            FUNCTION_WITH_COMMA = "FUNCTION_WITH_COMMA"
            FUNCTION_WITHOUT_COMMA = "FUNCTION_WITHOUT_COMMA"
            NORMAL = "NORMAL"

        def _has_semicolon(start_index: int) -> bool:
            r"""
            Checks if function parameters are separated by `;`.
            Traverses the expression content to find the delimiter format for the current function parameters.

            :param start_index: Index to start the check.
            :return: Whether `;` is used as a delimiter.
            """
            bracket_count = 1
            for exp_index in range(start_index, len(self.expression)):
                exp_char = self.expression[exp_index]
                if exp_char == '(':
                    bracket_count += 1
                elif exp_char == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return False  # Found matching right parenthesis, no `;` delimiter detected
                elif exp_char == ';' and bracket_count == 1:
                    return True  # Detected `;` at the current bracket level
            return False

        # Initialize variables
        stack = []  # Tracks nested block types
        invalid_positions = []  # Records invalid numeric separator positions
        result = []  # List of characters for the final result
        i = 0  # Current character index

        # Main loop to traverse the characters in the expression
        while i < len(self.expression):
            char = self.expression[i]

            # Check if it's the start of a function name
            matched_function = next(
                (
                    fn for fn in function_names
                    if self.expression.startswith(fn, i) and i + len(fn) < len(self.expression) and
                    self.expression[i + len(fn)] == '('
                ),
                None,
            )

            if matched_function:
                result.append(matched_function)
                i += len(matched_function)
                continue

            # Handle left parenthesis
            if char == '(':
                # Check if it's a function's left parenthesis
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

            # Handle right parenthesis
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
                # Check if it's inside a function
                if not (stack and stack[-1][0] in {BlockType.FUNCTION_WITH_COMMA, BlockType.FUNCTION_WITHOUT_COMMA}):
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_SEPARATOR_OUTSIDE,
                        expression=self.expression,
                        positions=[i],
                        primary_info=';',
                        secondary_info='Captured during preprocessing of digit delimiter conversions'
                    )
                i += 1
                continue

            # Add other characters directly to the result
            result.append(char)
            i += 1

        # Raise an exception if invalid numeric separators are found
        if invalid_positions:
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.NUMERIC_SEPARATOR_ERROR,
                expression=self.expression,
                positions=invalid_positions,
            )

        # Update the expression
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

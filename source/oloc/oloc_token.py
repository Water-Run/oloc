r"""
:author: WaterRun
:date: 2025-04-04
:file: oloc_token.py
:description: oloc token
"""

import oloc_utils as utils
from oloc_exceptions import *


class Token:
    r"""
    A token in an expression.
    :param token_type: The category of the token
    :param token_range: The range (position) of the token in the expression
    :param token_value: The actual value of the token
    """

    class TYPE(Enum):
        r"""
        Enumeration of all possible token types
        """
        # Number types
        PERCENTAGE = 'Percentage'  # Percentage: 100%
        INFINITE_DECIMAL = 'InfiniteRecurringDecimal'  # Infinite decimal: 3.3... or 2.3:4
        FINITE_DECIMAL = 'FiniteDecimal'  # Finite decimal: 3.14
        INTEGER = 'Integer'  # Integer: 42

        # Irrational number types
        NATIVE_IRRATIONAL = 'NativeIrrationalNumber'  # Native irrational numbers: π, e
        SHORT_CUSTOM = 'ShortCustomIrrational'  # Short custom irrational numbers: x, y
        LONG_CUSTOM = 'LongCustomIrrational'  # Long custom irrational numbers: <name>

        # Irrational parameter type
        IRRATIONAL_PARAM = 'IrrationalParam'

        # Operators
        OPERATOR = 'Operator'  # Operators: +, -, *, /, etc.
        LBRACKET = 'LeftBracket'  # Left brackets: (, [, {
        RBRACKET = 'RightBracket'  # Right brackets: ), ], }

        # Function-related
        FUNCTION = 'Function'  # Functions: sin, pow, etc.
        PARAM_SEPARATOR = 'ParameterSeparator'  # Parameter separators: , or ;

        # Unknown type
        UNKNOWN = 'Unknown'  # Unrecognized characters

    def __init__(self, token_type: TYPE, token_value: str = "", token_range: list[int, int] = None):
        if token_range is None:
            token_range = [0, 0]
        self.value = token_value
        if self.value == "":
            self.type = Token.TYPE.UNKNOWN
        self.type = token_type
        self.range = token_range
        self.is_legal = False
        self._check_legal()

    def __repr__(self):
        return f"Token('{self.type.value}', '{self.value}', '{self.range}')"

    def get_exception_type(self) -> OlocValueError.TYPE:
        r"""
        Returns the corresponding OlocValueError.TYPE
        :return:
        """
        mapping = {
            Token.TYPE.PERCENTAGE: OlocValueError.TYPE.INVALID_PERCENTAGE,
            Token.TYPE.INFINITE_DECIMAL: OlocValueError.TYPE.INVALID_INFINITE_DECIMAL,
            Token.TYPE.FINITE_DECIMAL: OlocValueError.TYPE.INVALID_FINITE_DECIMAL,
            Token.TYPE.INTEGER: OlocValueError.TYPE.INVALID_INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL: OlocValueError.TYPE.INVALID_NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM: OlocValueError.TYPE.INVALID_SHORT_CUSTOM_IRRATIONAL,
            Token.TYPE.LONG_CUSTOM: OlocValueError.TYPE.INVALID_LONG_CUSTOM_IRRATIONAL,
            Token.TYPE.OPERATOR: OlocValueError.TYPE.INVALID_OPERATOR,
            Token.TYPE.LBRACKET: OlocValueError.TYPE.INVALID_BRACKET,
            Token.TYPE.RBRACKET: OlocValueError.TYPE.INVALID_BRACKET,
            Token.TYPE.FUNCTION: OlocValueError.TYPE.INVALID_FUNCTION,
            Token.TYPE.PARAM_SEPARATOR: OlocValueError.TYPE.INVALID_PARAM_SEPARATOR,
            Token.TYPE.IRRATIONAL_PARAM: OlocValueError.TYPE.INVALID_IRRATIONAL_PARAM,
            Token.TYPE.UNKNOWN: OlocValueError.TYPE.UNKNOWN_TOKEN,
        }
        return mapping[self.type]

    def _check_legal(self) -> bool:
        r"""
        Checks the legality of the token itself.
        :return: Whether the token is valid
        """
        # Call the corresponding check method based on the token type
        checker_method_name = f"_check_{self.type.name.lower()}"
        if hasattr(self, checker_method_name):
            checker_method = getattr(self, checker_method_name)
            self.is_legal = checker_method()
        else:
            self.is_legal = False
        return self.is_legal

    def _check_integer(self) -> bool:
        r"""
        Checks the legality of an integer-type token.
        :return: Whether it is valid
        """

        return self.value.isdigit() and (self.value == '0' or not self.value.startswith('0'))

    def _check_finite_decimal(self) -> bool:
        r"""
        Checks the legality of a finite decimal token.
        :return: Whether it is valid
        """
        if '.' in self.value:
            parts = self.value.split('.')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return True
        return False

    def _check_infinite_decimal(self) -> bool:
        r"""
        Checks the legality of an infinite decimal token.
        :return: Whether it is valid
        """
        # Case 1: Ends with 3-6 dots, e.g., 3.14...
        if '.' in self.value and self.value.endswith(('...', '....', '.....', '......')):
            base = self.value.rstrip('.')
            if '.' in base:
                parts = base.split('.')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return True

        # Case 2: Ends with : and an integer, e.g., 2.3:4
        if ':' in self.value:
            parts = self.value.split(':')
            if len(parts) == 2:
                decimal_part, integer_part = parts
                if '.' in decimal_part:
                    decimal_parts = decimal_part.split('.')
                    if len(decimal_parts) == 2 and decimal_parts[0].isdigit() and decimal_parts[1].isdigit():
                        if integer_part.isdigit():
                            return True

        return False

    def _check_percentage(self) -> bool:
        r"""
        Checks the legality of a percentage token.
        :return: Whether it is valid
        """
        if self.value.endswith('%'):
            number_part = self.value[:-1]
            if '.' in number_part:
                parts = number_part.split('.')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    return True
            elif number_part.isdigit():
                return True
        return False

    def _check_native_irrational(self) -> bool:
        r"""
        Checks the legality of a native irrational number token.
        :return: Whether it is valid
        """
        if self.value in {'π', '𝑒'}:
            return True
        return False

    def _check_short_custom(self) -> bool:
        r"""
        Checks the legality of a short custom irrational number token.
        :return: Whether it is valid
        """
        if self.value in set(utils.get_symbol_mapping_table().keys()):
            return False
        return True

    def _check_long_custom(self) -> bool:
        r"""
        Checks the legality of a long custom irrational number token.
        :return: Whether it is valid
        """
        if not self.value.startswith("<") and self.value.endswith(">"):
            return False
        return True

    def _check_operator(self) -> bool:
        r"""
        Checks the legality of an operator token.
        :return: Whether it is valid
        """

        symbol_mapping_table = utils.get_symbol_mapping_table()
        # Exclude grouping operators
        brackets = ['(', ')', '[', ']', '{', '}']

        # Check if it is in the symbol mapping table and not a bracket
        return self.value in symbol_mapping_table.keys() and self.value not in brackets

    def _check_lbracket(self) -> bool:
        r"""
        Checks the legality of a left bracket token.
        :return: Whether it is valid
        """
        return self.value in ['(', '[', '{']

    def _check_rbracket(self) -> bool:
        r"""
        Checks the legality of a right bracket token.
        :return: Whether it is valid
        """
        return self.value in [')', ']', '}']

    def _check_param_separator(self) -> bool:
        r"""
        Checks the legality of a parameter separator token.
        :return: Whether it is valid
        """
        return self.value in [',', ';']

    def _check_function(self) -> bool:
        r"""
        Checks the legality of a function token.
        :return: Whether it is valid
        """

        function_list = utils.get_function_name_list()
        return self.value in function_list

    def _check_irrational_param(self) -> bool:
        r"""
        Checks the legality of an irrational parameter token.
        :return: Whether it is valid
        """
        if len(self.value) <= 1:
            return False

        # Check if the value ends with "?"
        if not self.value.endswith("?"):
            return False

        # Initialize the decimal point flag
        find_decimal_point = False
        # Check if the first character is "+" or "-"
        start_index = 1 if self.value[0] in "+-" else 0

        # Iterate through each character in the string (skipping the first if it's a sign)
        for c in self.value[start_index:-1]:
            if c == '.':
                # If a decimal point is already found, return False
                if find_decimal_point:
                    return False
                # Mark the decimal point as found
                find_decimal_point = True
            elif not c.isdigit():
                # If the character is not a digit, return False
                return False

        return True

    def is_bracket(self) -> bool:
        r"""
        Determine if a Token is a parenthesis
        :return: True if Token is a parenthesis, False otherwise
        """
        return self.type in (Token.TYPE.LBRACKET, Token.TYPE.RBRACKET)

    def is_number(self) -> bool:
        r"""
        Determine if a Token is a number
        :return: True if Token is a number, False otherwise
        """
        return self.type in (Token.TYPE.INTEGER,
                             Token.TYPE.FINITE_DECIMAL, Token.TYPE.INFINITE_DECIMAL, Token.TYPE.PERCENTAGE,
                             Token.TYPE.NATIVE_IRRATIONAL, Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM)

    def is_rational(self) -> bool:
        r"""
        Determine if a Token is a rational
        :return: True if Token is a rational, False otherwise
        """
        return self.type in (Token.TYPE.INTEGER,
                             Token.TYPE.FINITE_DECIMAL, Token.TYPE.INFINITE_DECIMAL, Token.TYPE.PERCENTAGE)

    def is_irrational(self) -> bool:
        r"""
        Determine if a Token is an irrational
        :return: True if Token is an irrational, False otherwise
        """
        return self.type in (Token.TYPE.NATIVE_IRRATIONAL, Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM)

    def is_valid_type_in_static_check(self) -> bool:
        r"""
        Determine if a Token is valid type in static check
        :return: True if Token is valid type in static check, False otherwise
        """
        return self.type in (
            Token.TYPE.INTEGER,
            Token.TYPE.OPERATOR,
            Token.TYPE.RBRACKET,
            Token.TYPE.LBRACKET,
            Token.TYPE.LONG_CUSTOM,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.IRRATIONAL_PARAM,
            Token.TYPE.FUNCTION,
            Token.TYPE.PARAM_SEPARATOR,
        )

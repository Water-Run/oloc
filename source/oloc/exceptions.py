r"""
:author: WaterRun
:date: 2025-03-01
:file: exceptions.py
:description: Oloc exceptions
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class OlocException(ABC, Exception):
    r"""
    Abstract base class for all Oloc exceptions.

    This class provides a standard structure for exception messages,
    requiring subclasses to define an exception type enumeration.
    """

    @abstractmethod
    class ExceptionType(Enum):
        r"""
        Abstract inner class for exception types.

        Subclasses must define this enum to provide specific messages
        and context information for their exception types.
        """
        ...

    def __init__(self, exception_type: Enum, expression: str, positions: List[int]):
        r"""
        Initialize the exception with a specific error type, the expression,
        and the positions of the issues.

        :param exception_type: The type of the exception (Enum)
        :param expression: The original expression
        :param positions: The positions of the issues in the expression
        """
        self.exception_type = exception_type
        self.expression = expression
        self.positions = positions
        super().__init__(self.__str__())

    def __str__(self):
        r"""
        Generate a detailed string representation of the exception.

        :return: A formatted string describing the error.
        """
        marker_line = self._generate_marker_line()
        return (
            f"{self.exception_type.value[0]}\n"
            f"{self.expression}\n"
            f"{marker_line}\n"
            f"Note: {self.exception_type.value[1]}"
        )

    def _generate_marker_line(self) -> str:
        r"""
        Generate a line with '^' markers at the specified positions.

        :return: A string with markers indicating the error positions.
        """
        marker_line = [' '] * len(self.expression)
        for pos in self.positions:
            if 0 <= pos < len(self.expression):
                marker_line[pos] = '^'
        return ''.join(marker_line)


class OlocFreeCommentException(OlocException):
    r"""
    Exception raised for unmatched '#' in free comments.
    """

    class ExceptionType(Enum):
        r"""
        Enum class defining the types of OlocFreeCommentException.
        """
        MISMATCH = (
            "OlocFreeCommentException: Mismatch '#' detected",
            "The content of free comments should be wrapped in a before and after '#'."
        )
        # Add more specific types of free comment errors here if needed.

    def __init__(self, exception_type: ExceptionType, expression: str, positions: List[int]):
        r"""
        Initialize the OlocFreeCommentException.

        :param exception_type: The type of the exception (Enum)
        :param expression: The original expression
        :param positions: The positions of the issues in the expression
        """
        super().__init__(exception_type, expression, positions)

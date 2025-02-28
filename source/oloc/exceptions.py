r"""
:author: WaterRun
:date: 2025-02-28
:file: exceptions.py
:description: Oloc exceptions
"""

from abc import ABC, abstractmethod


class OlocException(ABC, Exception):
    """
    Abstract base class for all Oloc exceptions.

    This class provides a standard structure for exception messages,
    requiring subclasses to define a context message.
    """

    def __init__(self, message: str, expression: str, position: int):
        """
        Initialize the exception with a specific error message, the expression,
        and the position of the issue.

        :param message: The error message
        :param expression: The original expression
        :param position: The position of the issue in the expression
        """
        self.message = message
        self.expression = expression
        self.position = position
        super().__init__(self.__str__())

    def __str__(self):
        """
        Generate a detailed string representation of the exception.

        :return: A formatted string describing the error.
        """
        marker_line = ' ' * self.position + '^'
        return (
            f"{self.message}\n"
            f"{self.expression}\n"
            f"{marker_line}\n"
            f"{self._get_context_message()}"
        )

    @abstractmethod
    def _get_context_message(self) -> str:
        """
        Abstract method to provide additional context for the exception.

        Subclasses must implement this method to provide specific context
        messages related to the error.

        :return: A string with additional context about the exception.
        """
        pass


class OlocFreeCommentException(OlocException):
    """Exception raised for unmatched '#' in free comments."""

    def _get_context_message(self) -> str:
        """
        Provide a specific context message for free comment issues.

        :return: A string describing the issue with free comments.
        """
        return "The content of free comments should be wrapped in a before and after '#'."

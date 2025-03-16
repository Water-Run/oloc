r"""
:author: WaterRun
:date: 2025-03-16
:file: oloc_parser.py
:description: Oloc parser
"""

from oloc_token import Token


class Parser:
    r"""
    语法分析器

    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        ...

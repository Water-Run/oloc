r"""
:author: WaterRun
:date: 2025-03-24
:file: oloc_parser.py
:description: Oloc parser
"""

from oloc_token import Token
from enum import Enum


class ASTNode:
    r"""
    AST树的节点
    :param token: 创建节点的Token
    :param children: 子节点列表，用于嵌套结构
    """

    def __init__(self, token: Token, children: list[Token] | None = None):
        self.token = token
        self.children = children or []

    def __repr__(self):
        return f"ASTNode({self.token})\n[children]{self.children}"


class ASTTree:
    r"""
    AST树
    """

    def __init__(self):
        ...


class Parser:
    r"""
    语法分析器

    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        ...

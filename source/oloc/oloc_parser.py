r"""
:author: WaterRun
:date: 2025-03-22
:file: oloc_parser.py
:description: Oloc parser
"""

from oloc_token import Token


class ASTNode:
    r"""
    AST树的节点
    :param node_type: 节点类型，例如 "number", "operator", "function"
    :param value: 节点的值，例如数字值或操作符
    :param children: 子节点列表，用于嵌套结构
    """
    def __init__(self, node_type, value=None, children=None):
        self.node_type = node_type  # 节点类型
        self.value = value          # 节点的值
        self.children = children or []  # 子节点列表（默认为空）

    def __repr__(self):
        return f"ASTNode(type={self.node_type}, value={self.value}, children={self.children})"

class Parser:
    r"""
    语法分析器

    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        ...

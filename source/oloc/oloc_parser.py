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
    :param node_type: 节点的类型
    :param token: 创建节点的Token
    :param children: 子节点列表，用于嵌套结构
    """

    class TYPE(Enum):
        r"""
        AST节点的类型
        """
        BIN_EXP = 'BinaryExpression'
        LITERAL = 'Literal'
        FUN_CAL = 'FunctionCall'
        GRP_EXP = 'GroupExpression'
        URY_EXP = 'UnaryExpression'

    def __init__(self, node_type: TYPE, token: Token, children: list[Token] | None = None):
        self.type = node_type
        self.token = token
        self.children = children or []

    def add_child(self, child: Token):
        r"""
        添加子节点
        :param child: 子节点的Token
        :return: None
        """
        self.children.append(child)

    def __repr__(self):
        return f"ASTNode: {self.type}\n{self.token}\n{self.children}"


class ASTTree:
    r"""
    AST树
    :param root: 根节点
    """

    def __init__(self, root: ASTNode):
        self.root = root

    def __repr__(self):

        result = "ASTTree:\n"

        def _traverse(node=None, depth=0):
            """
            遍历树 (前序遍历)，打印结构
            :param node: 当前节点
            :param depth: 当前深度
            """
            if node is None:
                node = self.root
            nonlocal result
            result += ("  " * depth + f"{node.node_type}: {node.value}")
            for child in node.children:
                _traverse(child, depth + 1)

        return result


class Parser:
    r"""
    语法分析器

    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        ...

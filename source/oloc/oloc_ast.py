r"""
:author: WaterRun
:date: 2025-04-01
:file: oloc_core.py
:description: Oloc ast
"""

from enum import Enum
from oloc_token import Token


class ASTNode:
    r"""
    抽象语法树节点
    :param node_type: 节点的类型
    :param tokens: 节点包含的Token流
    """

    class TYPE(Enum):
        r"""
        节点类型
        """
        BIN_EXP = 'BinaryExpression'  # 二元表达式
        URY_EXP = 'UnaryExpression'   # 一元表达式
        LITERAL = 'Literal'           # 字面量
        FUN_CAL = 'FunctionCall'      # 函数调用
        GRP_EXP = 'GroupExpression'   # 分组表达式

    def __init__(self, node_type: TYPE, tokens: list[Token] = None):
        self.type = node_type
        self.tokens = tokens or []
        self.children = []
        self.parent = None

    def add_child(self, child: 'ASTNode') -> None:
        r"""
        添加子节点
        :param child: 要添加的子节点
        :return: None
        """
        if child:
            self.children.append(child)
            child.parent = self

    def __repr__(self):
        r"""
        节点的字符串表示
        :return: 字符串
        """
        token_val = ""
        if self.tokens:
            if len(self.tokens) == 1:
                token_val = f"({self.tokens[0].value})"
            else:
                token_val = f"({[t.value for t in self.tokens]})"

        return f"{self.type.value}{token_val}"


class ASTTree:
    r"""
    抽象语法树
    :param root: 根节点
    """

    def __init__(self, root: ASTNode = None):
        self.root = root
        self.node_count = 0 if root is None else self._count_nodes(root)

    def _count_nodes(self, node: ASTNode) -> int:
        r"""
        计算节点数量
        :param node: 起始节点
        :return: 节点数量
        """
        if not node:
            return 0

        count = 1  # 当前节点
        for child in node.children:
            count += self._count_nodes(child)

        return count

    def __repr__(self):
        r"""
        树的字符串表示，以可视化形式展示
        :return: 字符串
        """
        if not self.root:
            return f"AST: {self._count_nodes(self.root)} node\n(Empty)"

        lines = [f"AST: {self._count_nodes(self.root)} node"]
        self._build_tree_string(self.root, "", True, lines)
        return "\n".join(lines)

    def _build_tree_string(self, node: ASTNode, prefix: str, is_last: bool, lines: list):
        r"""
        构建树的字符串表示
        :param node: 当前节点
        :param prefix: 前缀字符串
        :param is_last: 是否是父节点的最后一个子节点
        :param lines: 结果行列表
        :return: None
        """
        if not node:
            return

        # 确定当前行的连接符
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{node}")

        # 为子节点准备前缀
        new_prefix = prefix + ("    " if is_last else "│   ")

        # 递归处理所有子节点
        for i, child in enumerate(node.children):
            is_last_child = i == len(node.children) - 1
            self._build_tree_string(child, new_prefix, is_last_child, lines)

    def _traverse_node(self, node: ASTNode, order: str, result: list):
        r"""
        遍历节点
        :param node: 当前节点
        :param order: 遍历顺序
        :param result: 结果列表
        :return: None
        """
        if not node:
            return

        if order == "pre":
            result.append(node)

        # 递归遍历子节点
        for child in node.children:
            self._traverse_node(child, order, result)

        if order == "post":
            result.append(node)

        # 中序遍历只对二元表达式有意义，其他节点类型视为前序遍历
        if order == "in":
            if node.type == ASTNode.TYPE.BIN_EXP and len(node.children) == 2:
                if len(result) > 0 and result[-1] == node.children[0]:
                    result.append(node)
            elif node not in result:
                result.append(node)

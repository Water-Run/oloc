r"""
:author: WaterRun
:date: 2025-04-22
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

import time
from enum import Enum, auto

from oloc_token import Token
from oloc_ast import ASTTree, ASTNode
from oloc_lexer import Lexer
from oloc_exceptions import *


class CalcEvent:
    r"""
    计算事件类，用于记录计算过程中的事件
    """
    class Type(Enum):
        r"""计算事件类型"""
        NODE_EVAL_START = auto()  # 节点开始计算
        NODE_EVAL_COMPLETE = auto()  # 节点计算完成
        STEP_COMPLETE = auto()  # 计算步骤完成

    def __init__(self, event_type: Type, node: ASTNode = None, result: list[Token] = None, description: str = None):
        r"""
        初始化计算事件
        :param event_type: 事件类型
        :param node: 相关的AST节点
        :param result: 计算结果
        :param description: 事件描述
        """
        self.type = event_type
        self.node = node
        self.result = result
        self.description = description


class Evaluator:
    r"""
    求值器
    :param expression: 构建的表达式. 该参数应该和Parser阶段一致
    :param tokens: 构建的Token流. 该参数应该和Parser阶段一致
    :param ast: 构建的AST树
    """

    def __init__(self, expression: str, tokens: list[Token], ast: ASTTree):
        self.expression = expression
        self.tokens = tokens
        self.ast = ast
        self.result: list[list[Token]] = []  # 清空结果列表，不再使用初始tokens
        self.time_cost = -1

        # 为新的计算步骤生成机制添加的属性
        self.calculation_events = []  # 记录计算事件
        self.node_results = {}  # 记录节点计算结果，键为节点ID，值为Token列表
        self.node_original = {}  # 记录节点原始表示，键为节点ID，值为Token列表
        self.eval_order = []  # 记录节点的计算顺序，存储节点ID

    def __repr__(self):
        result = (f"Evaluator: \n"
                  f"expression: {self.expression}\n"
                  f"expression (split between token): ")
        for token in self.tokens:
            result += f"{token.value} "
        result += "\ntoken flow: \n"
        for index, token in enumerate(self.tokens):
            result += f"{index}\t{token}\n"
        result += f"ast: \n{self.ast}"
        result += "\n result:\n"
        for result_index, result_list in enumerate(self.result):
            result += f"{result_index}: {' '.join([t.value for t in result_list])}\n"
        result += f"\ntime cost: {'(Not execute)' if self.time_cost == -1 else self.time_cost / 1000000} ms\n"
        return result

    def _evaluate(self):
        r"""
        执行求值
        :return: None
        """
        # 清空事件和结果记录
        self.calculation_events = []
        self.node_results = {}
        self.node_original = {}
        self.eval_order = []
        self.result = []

        # 将原始表达式添加为第一步
        self.result.append(self.tokens.copy())

        # 递归求值AST树
        final_result = self._evaluate_node(self.ast.root)

        # 生成计算步骤
        self._generate_calculation_steps()

        # 确保最终结果与最后一步一致
        last_step = self.result[-1] if self.result else []
        last_step_str = ' '.join([t.value for t in last_step])
        final_result_str = ' '.join([t.value for t in final_result])

        if not self.result or last_step_str != final_result_str:
            self.result.append(final_result)

        # 更新表达式字符串和tokens
        self.tokens, self.expression = Lexer.update(final_result)

    def _evaluate_node(self, node: ASTNode) -> list[Token]:
        r"""
        递归评估AST节点，记录计算事件
        :param node: 要评估的节点
        :return: 计算结果的Token列表
        """
        # 为节点生成原始表示
        original_repr = self._generate_node_representation(node)
        self.node_original[id(node)] = original_repr

        # 记录节点开始计算的事件
        self.calculation_events.append(
            CalcEvent(CalcEvent.Type.NODE_EVAL_START, node, None)
        )

        result = None

        # 字面量节点
        if node.type == ASTNode.TYPE.LITERAL:
            result = [node.tokens[0]]

        # 分组表达式节点
        elif node.type == ASTNode.TYPE.GRP_EXP:
            if len(node.children) != 1:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [node.tokens[0].range[0] if node.tokens else 0],
                    primary_info=f"Group expression should have exactly one child, got {len(node.children)}"
                )

            # 计算括号内的表达式
            inner_result = self._evaluate_node(node.children[0])

            # 这里是关键变化：不再自动添加括号，直接返回内部结果
            # 括号会在必要时由上层方法添加
            result = inner_result

        # 二元表达式节点
        elif node.type == ASTNode.TYPE.BIN_EXP:
            if len(node.children) != 2:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [node.tokens[0].range[0] if node.tokens else 0],
                    primary_info=f"Binary expression should have exactly two children, got {len(node.children)}"
                )

            # 获取操作符
            op_token = None
            for token in node.tokens:
                if token.type == Token.TYPE.OPERATOR:
                    op_token = token
                    break

            if op_token is None:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [0],
                    primary_info="Binary expression missing operator"
                )

            # 计算左右子表达式
            left_result = self._evaluate_node(node.children[0])
            right_result = self._evaluate_node(node.children[1])

            # 根据操作符执行计算
            operator = op_token.value

            if operator == "+":
                result = Calculation.addition(left_result, right_result)
            elif operator == "-":
                result = Calculation.subtraction(left_result, right_result)
            elif operator == "*":
                result = Calculation.multiplication(left_result, right_result)
            elif operator == "/":
                result = Calculation.division(left_result, right_result)
            elif operator == "^":
                result = Function.Pow.pow(left_result, right_result)
            else:
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.UNSUPPORTED_OPERATOR,
                    self.expression,
                    [op_token.range[0]],
                    primary_info=f"Unsupported operator: {operator}"
                )

        # 一元表达式节点
        elif node.type == ASTNode.TYPE.URY_EXP:
            if len(node.children) != 1:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [node.tokens[0].range[0] if node.tokens else 0],
                    primary_info=f"Unary expression should have exactly one child, got {len(node.children)}"
                )

            # 获取操作符
            op_token = None
            for token in node.tokens:
                if token.type == Token.TYPE.OPERATOR:
                    op_token = token
                    break

            if op_token is None:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [0],
                    primary_info="Unary expression missing operator"
                )

            # 计算操作数
            operand_result = self._evaluate_node(node.children[0])

            # 应用一元运算符
            operator = op_token.value

            if operator == "-":
                result = Calculation.negate_expression(operand_result)
            elif operator == "+":
                result = operand_result  # 正号不改变值
            elif operator == "√":
                result = Function.Pow.sqrt(operand_result)
            else:
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.UNSUPPORTED_OPERATOR,
                    self.expression,
                    [op_token.range[0]],
                    primary_info=f"Unsupported unary operator: {operator}"
                )

        # 函数调用节点
        elif node.type == ASTNode.TYPE.FUN_CAL:
            # 获取函数名
            func_token = None
            for token in node.tokens:
                if token.type == Token.TYPE.FUNCTION:
                    func_token = token
                    break

            if func_token is None:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [0],
                    primary_info="Function call missing function name"
                )

            func_name = func_token.value

            # 计算所有参数
            args_results = []
            for child in node.children:
                arg_result = self._evaluate_node(child)
                args_results.append(arg_result)

            # 执行函数计算
            if func_name == "pow":
                if len(args_results) != 2:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[func_token.range[0]],
                        primary_info="pow",
                        secondary_info="expected 2 arguments"
                    )
                result = Function.Pow.pow(args_results[0], args_results[1])
            elif func_name == "sqrt":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[func_token.range[0]],
                        primary_info="sqrt",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sqrt(args_results[0])
            elif func_name == "sq":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[func_token.range[0]],
                        primary_info="sq",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sq(args_results[0])
            elif func_name == "cub":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[func_token.range[0]],
                        primary_info="cub",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.cub(args_results[0])
            elif func_name == "rec":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[func_token.range[0]],
                        primary_info="rec",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.rec(args_results[0])
            else:
                raise OlocCalculationError(
                    exception_type=OlocCalculationError.TYPE.UNSUPPORTED_FUNCTION,
                    expression=self.expression,
                    positions=[func_token.range[0]],
                    primary_info=func_name
                )

        # 未知节点类型
        else:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                self.expression,
                [0],
                primary_info=f"Unknown node type: {node.type}"
            )

        # 记录节点计算结果
        self.node_results[id(node)] = result

        # 记录节点完成计算的事件
        self.calculation_events.append(
            CalcEvent(CalcEvent.Type.NODE_EVAL_COMPLETE, node, result)
        )

        # 将节点ID添加到计算顺序列表
        self.eval_order.append(id(node))

        # 记录完成一个有意义的计算步骤
        self._record_calculation_step(node)

        return result

    def _generate_node_representation(self, node: ASTNode) -> list[Token]:
        r"""
        生成节点的原始表示，会自动移除冗余括号
        :param node: 要表示的节点
        :return: 表示节点的Token列表
        """
        if node.type == ASTNode.TYPE.LITERAL:
            # 字面量节点直接返回token
            return [node.tokens[0]]

        elif node.type == ASTNode.TYPE.GRP_EXP:
            # 分组表达式: (expr)
            if len(node.children) == 1:
                inner_repr = self._generate_node_representation(node.children[0])

                # 如果内部表达式只有一个token，不需要添加括号
                if len(inner_repr) == 1:
                    return inner_repr

                # 否则添加括号
                l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                return [l_bracket] + inner_repr + [r_bracket]
            else:
                return []

        elif node.type == ASTNode.TYPE.BIN_EXP:
            # 二元表达式: left op right
            if len(node.children) == 2:
                left_repr = self._generate_node_representation(node.children[0])
                right_repr = self._generate_node_representation(node.children[1])

                # 查找操作符
                op_token = None
                for token in node.tokens:
                    if token.type == Token.TYPE.OPERATOR:
                        op_token = token
                        break

                if op_token:
                    # 检查是否需要为左子表达式添加括号
                    left_needs_brackets = self._needs_brackets(node.children[0], op_token.value, "left")

                    # 检查是否需要为右子表达式添加括号
                    right_needs_brackets = self._needs_brackets(node.children[1], op_token.value, "right")

                    result = []

                    # 添加左子表达式，必要时添加括号
                    if left_needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        result.extend([l_bracket] + left_repr + [r_bracket])
                    else:
                        result.extend(left_repr)

                    # 添加操作符
                    result.append(op_token)

                    # 添加右子表达式，必要时添加括号
                    if right_needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        result.extend([l_bracket] + right_repr + [r_bracket])
                    else:
                        result.extend(right_repr)

                    return result
                else:
                    return []
            else:
                return []

        elif node.type == ASTNode.TYPE.URY_EXP:
            # 一元表达式: op expr
            if len(node.children) == 1:
                expr_repr = self._generate_node_representation(node.children[0])

                # 查找操作符
                op_token = None
                for token in node.tokens:
                    if token.type == Token.TYPE.OPERATOR:
                        op_token = token
                        break

                if op_token:
                    # 检查是否需要为表达式添加括号
                    expr_needs_brackets = self._needs_brackets_for_unary(node.children[0])

                    if expr_needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        return [op_token, l_bracket] + expr_repr + [r_bracket]
                    else:
                        return [op_token] + expr_repr
                else:
                    return []
            else:
                return []

        elif node.type == ASTNode.TYPE.FUN_CAL:
            # 函数调用: func(args)
            func_token = None
            for token in node.tokens:
                if token.type == Token.TYPE.FUNCTION:
                    func_token = token
                    break

            if func_token:
                result = [func_token, Token(Token.TYPE.LBRACKET, "(", [0, 0])]

                # 添加参数
                for i, child in enumerate(node.children):
                    if i > 0:
                        result.append(Token(Token.TYPE.SEPARATOR, ",", [0, 0]))
                    result.extend(self._generate_node_representation(child))

                result.append(Token(Token.TYPE.RBRACKET, ")", [0, 0]))
                return result
            else:
                return []

        # 其他类型节点
        return []

    def _needs_brackets(self, node: ASTNode, parent_op: str, position: str) -> bool:
        r"""
        判断节点是否需要括号
        :param node: 要判断的节点
        :param parent_op: 父节点的操作符
        :param position: 节点在父节点中的位置 ('left' 或 'right')
        :return: 是否需要括号
        """
        # 单个token不需要括号
        if node.type == ASTNode.TYPE.LITERAL:
            return False

        # 如果节点本身已经是分组表达式，不需要再加括号
        if node.type == ASTNode.TYPE.GRP_EXP:
            return False

        # 一元表达式通常不需要括号，除非作为幂的底数
        if node.type == ASTNode.TYPE.URY_EXP:
            return parent_op == "^" and position == "left"

        # 对于二元表达式，需要根据运算符优先级判断
        if node.type == ASTNode.TYPE.BIN_EXP:
            node_op = None
            for token in node.tokens:
                if token.type == Token.TYPE.OPERATOR:
                    node_op = token.value
                    break

            if node_op:
                # 根据运算符优先级判断是否需要括号
                return self._needs_brackets_by_precedence(node_op, parent_op, position)

        # 函数调用不需要括号
        if node.type == ASTNode.TYPE.FUN_CAL:
            return False

        # 默认情况，保守起见加括号
        return True

    def _needs_brackets_for_unary(self, node: ASTNode) -> bool:
        r"""
        判断一元表达式的操作数是否需要括号
        :param node: 要判断的节点
        :return: 是否需要括号
        """
        # 字面量不需要括号
        if node.type == ASTNode.TYPE.LITERAL:
            return False

        # 分组表达式不需要括号
        if node.type == ASTNode.TYPE.GRP_EXP:
            return False

        # 函数调用不需要括号
        if node.type == ASTNode.TYPE.FUN_CAL:
            return False

        # 二元表达式需要括号
        if node.type == ASTNode.TYPE.BIN_EXP:
            return True

        # 其他情况（包括嵌套的一元表达式）通常不需要括号
        return False

    def _needs_brackets_by_precedence(self, node_op: str, parent_op: str, position: str) -> bool:
        r"""
        根据运算符优先级判断是否需要括号
        :param node_op: 节点的运算符
        :param parent_op: 父节点的运算符
        :param position: 节点在父节点中的位置 ('left' 或 'right')
        :return: 是否需要括号
        """
        # 定义运算符优先级，数字越大优先级越高
        precedence = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
            "^": 3
        }

        # 获取优先级
        node_prec = precedence.get(node_op, 0)
        parent_prec = precedence.get(parent_op, 0)

        # 如果节点运算符优先级低于父节点，需要括号
        if node_prec < parent_prec:
            return True

        # 如果优先级相同，根据结合性和位置判断
        if node_prec == parent_prec:
            # 加减法和乘除法左结合，只有右侧需要括号
            if node_op in ["+", "-", "*", "/"] and parent_op in ["+", "-", "*", "/"] and position == "right" and node_op != parent_op:
                return True

            # 减法的特殊处理：左侧是减法时右侧需要括号
            if parent_op == "-" and position == "right":
                return True

            # 除法的特殊处理：左侧是除法时右侧需要括号
            if parent_op == "/" and position == "right":
                return True

            # 幂运算右结合，左侧需要括号
            if node_op == "^" and parent_op == "^" and position == "left":
                return True

        return False

    def _simplify_brackets(self, tokens: list[Token]) -> list[Token]:
        r"""
        简化表达式中不必要的括号
        :param tokens: 要简化的Token列表
        :return: 简化后的Token列表
        """
        # 如果只有一对括号包裹整个表达式，可以去除
        if (len(tokens) >= 3 and
            tokens[0].type == Token.TYPE.LBRACKET and tokens[0].value == "(" and
            tokens[-1].type == Token.TYPE.RBRACKET and tokens[-1].value == ")"):

            # 检查这对括号是否匹配
            bracket_level = 1
            for i in range(1, len(tokens) - 1):
                if tokens[i].type == Token.TYPE.LBRACKET and tokens[i].value == "(":
                    bracket_level += 1
                elif tokens[i].type == Token.TYPE.RBRACKET and tokens[i].value == ")":
                    bracket_level -= 1

                # 如果括号在中间就闭合了，说明最外层括号不是包裹整个表达式的
                if bracket_level == 0 and i < len(tokens) - 2:
                    return tokens

            # 最外层括号确实包裹了整个表达式，移除它们
            # 但需要检查内部表达式是否需要括号保护
            inner_tokens = tokens[1:-1]

            # 如果内部只有一个token或者是完整的函数调用，可以去括号
            if len(inner_tokens) == 1 or self._is_complete_function_call(inner_tokens):
                return inner_tokens

            # 如果内部是一个二元表达式，检查是否需要保留括号
            operator_pos = self._find_main_operator_position(inner_tokens)
            if operator_pos is not None:
                # 这是一个二元表达式，保留原样
                return tokens

        return tokens

    def _is_complete_function_call(self, tokens: list[Token]) -> bool:
        r"""
        检查token序列是否为完整的函数调用
        :param tokens: 要检查的Token列表
        :return: 是否为完整的函数调用
        """
        if len(tokens) < 3:
            return False

        if tokens[0].type != Token.TYPE.FUNCTION:
            return False

        if tokens[1].type != Token.TYPE.LBRACKET or tokens[1].value != "(":
            return False

        if tokens[-1].type != Token.TYPE.RBRACKET or tokens[-1].value != ")":
            return False

        # 检查括号是否匹配
        bracket_level = 1
        for i in range(2, len(tokens) - 1):
            if tokens[i].type == Token.TYPE.LBRACKET and tokens[i].value == "(":
                bracket_level += 1
            elif tokens[i].type == Token.TYPE.RBRACKET and tokens[i].value == ")":
                bracket_level -= 1

            if bracket_level == 0:
                return False

        return True

    def _find_main_operator_position(self, tokens: list[Token]) -> int:
        r"""
        查找表达式中主操作符的位置
        :param tokens: 要查找的Token列表
        :return: 主操作符的位置，未找到则返回None
        """
        # 跟踪括号层级
        bracket_level = 0
        # 操作符候选及其位置
        operators = []

        for i, token in enumerate(tokens):
            if token.type == Token.TYPE.LBRACKET and token.value == "(":
                bracket_level += 1
            elif token.type == Token.TYPE.RBRACKET and token.value == ")":
                bracket_level -= 1
            elif token.type == Token.TYPE.OPERATOR and bracket_level == 0:
                operators.append((i, token.value))

        if not operators:
            return None

        # 按运算符优先级排序
        precedence = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
            "^": 3
        }

        # 找出最低优先级的运算符
        min_prec = min(precedence.get(op[1], 0) for op in operators)
        candidates = [op for op in operators if precedence.get(op[1], 0) == min_prec]

        # 对于相同优先级，选择最后出现的加减，最先出现的乘除
        if min_prec == 1:  # 加减法
            return candidates[-1][0]  # 最后出现的
        else:
            return candidates[0][0]  # 最先出现的

    def _record_calculation_step(self, node: ASTNode):
        r"""
        记录一个有意义的计算步骤
        :param node: 完成计算的节点
        """
        # 检查节点类型，确定是否需要记录步骤
        if node.type == ASTNode.TYPE.LITERAL:
            # 字面量节点不需要记录步骤
            return

        # 检查节点是否有原始表示和计算结果
        if id(node) not in self.node_original or id(node) not in self.node_results:
            return

        original = self.node_original[id(node)]
        result = self.node_results[id(node)]

        # 检查计算是否有变化
        if self._tokens_equal(original, result):
            # 计算前后没有变化，不记录步骤
            return

        # 创建步骤完成事件
        self.calculation_events.append(
            CalcEvent(CalcEvent.Type.STEP_COMPLETE, node, result)
        )

    def _generate_calculation_steps(self):
        r"""
        根据计算事件生成计算步骤
        """
        # 第一步已经是原始表达式，从第二步开始生成

        # 获取所有步骤完成事件
        step_events = [event for event in self.calculation_events
                       if event.type == CalcEvent.Type.STEP_COMPLETE]

        # 按照计算的顺序排序步骤
        step_events.sort(key=lambda e: self.eval_order.index(id(e.node)))

        # 为嵌套函数和表达式处理特殊情况
        processed_steps = self._process_nested_steps(step_events)

        # 使用集合记录已添加的步骤表达式，避免重复
        added_steps = set()
        added_steps.add(self._tokens_to_str(self.result[0]))

        # 生成每一步的表达式
        for step_event in processed_steps:
            node = step_event.node
            result = step_event.result

            # 生成该步骤的完整表达式
            step_expr = self._generate_step_expression(node, result)

            # 简化表达式中不必要的括号
            step_expr = self._simplify_expression(step_expr)

            # 转换为字符串，检查是否重复
            step_expr_str = self._tokens_to_str(step_expr)

            # 添加到结果列表，避免重复
            if step_expr and step_expr_str not in added_steps:
                self.result.append(step_expr)
                added_steps.add(step_expr_str)

    def _simplify_expression(self, expr: list[Token]) -> list[Token]:
        r"""
        简化表达式，移除冗余括号并规范化
        :param expr: 要简化的表达式
        :return: 简化后的表达式
        """
        # 首先尝试删除最外层冗余括号
        expr = self._remove_redundant_brackets(expr)

        # 然后递归地简化内部括号表达式
        return self._recursive_simplify_brackets(expr)

    def _remove_redundant_brackets(self, tokens: list[Token]) -> list[Token]:
        r"""
        移除最外层冗余的括号
        :param tokens: 要处理的Token列表
        :return: 处理后的Token列表
        """
        # 检查是否整个表达式被一对括号包裹
        if len(tokens) < 3:
            return tokens

        if tokens[0].type != Token.TYPE.LBRACKET or tokens[0].value != "(" or tokens[-1].type != Token.TYPE.RBRACKET or tokens[-1].value != ")":
            return tokens

        # 检查开头的左括号是否与结尾的右括号匹配
        bracket_level = 1
        for i in range(1, len(tokens) - 1):
            if tokens[i].type == Token.TYPE.LBRACKET and tokens[i].value == "(":
                bracket_level += 1
            elif tokens[i].type == Token.TYPE.RBRACKET and tokens[i].value == ")":
                bracket_level -= 1

            # 如果括号提前匹配完成，说明最外层括号不是包裹整个表达式
            if bracket_level == 0 and i < len(tokens) - 1:
                return tokens

        # 如果表达式只有一个token，或者是函数调用，或者是复杂表达式，保留括号
        inner_tokens = tokens[1:-1]

        # 如果内部只有单个token，可以移除括号
        if len(inner_tokens) == 1:
            return inner_tokens

        # 判断内部是否是单一优先级的表达式
        main_op_pos = self._find_main_operator_position(inner_tokens)
        if main_op_pos is not None:
            # 有主操作符，这是一个可以不加括号的完整表达式
            return inner_tokens

        # 如果内部是函数调用或者其他无法确定的结构，保留括号
        return tokens

    def _recursive_simplify_brackets(self, tokens: list[Token]) -> list[Token]:
        r"""
        递归地简化表达式中的括号
        :param tokens: 要简化的Token列表
        :return: 简化后的Token列表
        """
        if len(tokens) <= 1:
            return tokens

        result = []
        i = 0

        while i < len(tokens):
            if tokens[i].type == Token.TYPE.LBRACKET and tokens[i].value == "(":
                # 找到括号封闭的子表达式
                bracket_level = 1
                start_pos = i

                for j in range(i + 1, len(tokens)):
                    if tokens[j].type == Token.TYPE.LBRACKET and tokens[j].value == "(":
                        bracket_level += 1
                    elif tokens[j].type == Token.TYPE.RBRACKET and tokens[j].value == ")":
                        bracket_level -= 1

                    if bracket_level == 0:
                        # 找到匹配的右括号
                        sub_expr = tokens[start_pos:j+1]
                        # 简化子表达式的括号
                        simplified_sub = self._remove_redundant_brackets(sub_expr)

                        # 递归简化简化后的子表达式
                        if len(simplified_sub) > 1:
                            simplified_sub = self._recursive_simplify_brackets(simplified_sub)

                        result.extend(simplified_sub)
                        i = j + 1
                        break
                else:
                    # 未找到匹配的右括号，保留原样
                    result.append(tokens[i])
                    i += 1
            elif tokens[i].type == Token.TYPE.FUNCTION:
                # 处理函数调用
                result.append(tokens[i])
                i += 1

                # 找到函数的参数列表
                if i < len(tokens) and tokens[i].type == Token.TYPE.LBRACKET:
                    result.append(tokens[i])  # 添加左括号
                    i += 1

                    bracket_level = 1
                    while i < len(tokens) and bracket_level > 0:
                        if tokens[i].type == Token.TYPE.LBRACKET:
                            bracket_level += 1
                        elif tokens[i].type == Token.TYPE.RBRACKET:
                            bracket_level -= 1

                        result.append(tokens[i])
                        i += 1

                    # 函数调用处理完毕
                    continue
            else:
                # 其他token直接添加
                result.append(tokens[i])
                i += 1

        return result

    def _process_nested_steps(self, step_events: list[CalcEvent]) -> list[CalcEvent]:
        r"""
        处理嵌套函数和表达式的步骤，确保中间步骤不被跳过
        :param step_events: 原始步骤事件列表
        :return: 处理后的步骤事件列表
        """
        processed_events = []

        # 为函数调用添加中间步骤
        for event in step_events:
            node = event.node

            if node.type == ASTNode.TYPE.FUN_CAL and len(node.children) > 0:
                # 查找所有参数的计算结果
                for child in node.children:
                    if id(child) in self.node_results:
                        # 创建参数计算的中间步骤
                        func_token = None
                        for token in node.tokens:
                            if token.type == Token.TYPE.FUNCTION:
                                func_token = token
                                break

                        if func_token:
                            # 使用参数计算结果替换原始参数，生成中间步骤
                            intermediate_expr = self._generate_function_with_arg_results(
                                node, func_token, child
                            )

                            # 创建中间步骤事件
                            processed_events.append(
                                CalcEvent(
                                    CalcEvent.Type.STEP_COMPLETE,
                                    node,
                                    intermediate_expr
                                )
                            )

            # 添加原始事件
            processed_events.append(event)

        return processed_events

    def _generate_function_with_arg_results(self,
                                          func_node: ASTNode,
                                          func_token: Token,
                                          arg_node: ASTNode) -> list[Token]:
        r"""
        为函数调用生成带有参数计算结果的中间表示
        :param func_node: 函数调用节点
        :param func_token: 函数名token
        :param arg_node: 已计算的参数节点
        :return: 中间表示的Token列表
        """
        result = [func_token, Token(Token.TYPE.LBRACKET, "(", [0, 0])]

        for i, child in enumerate(func_node.children):
            if i > 0:
                result.append(Token(Token.TYPE.SEPARATOR, ",", [0, 0]))

            # 使用计算后的结果替换已计算的参数
            if child == arg_node and id(child) in self.node_results:
                result.extend(self.node_results[id(child)])
            else:
                # 其他参数使用原始表示
                if id(child) in self.node_original:
                    result.extend(self.node_original[id(child)])

        result.append(Token(Token.TYPE.RBRACKET, ")", [0, 0]))
        return result

    def _generate_step_expression(self, node: ASTNode, result: list[Token]) -> list[Token]:
        r"""
        生成计算步骤的完整表达式，替换对应节点的计算结果
        :param node: 计算完成的节点
        :param result: 节点的计算结果
        :return: 完整的表达式Token列表
        """
        # 从原始表达式开始
        original_expr = self.tokens.copy()

        # 使用AST进行递归替换
        return self._recursive_replace(self.ast.root, node, result, original_expr)

    def _recursive_replace(self,
                          current: ASTNode,
                          target: ASTNode,
                          replacement: list[Token],
                          expr: list[Token]) -> list[Token]:
        r"""
        递归替换表达式中的节点
        :param current: 当前遍历的节点
        :param target: 要替换的目标节点
        :param replacement: 替换内容
        :param expr: 当前表达式
        :return: 替换后的表达式
        """
        # 如果当前节点就是目标节点，直接返回替换内容
        if current == target:
            return replacement

        # 如果当前节点已经计算过，使用其结果
        if id(current) in self.node_results:
            # 特殊情况处理：如果当前节点包含目标节点，需要进一步递归
            contains_target = False
            for child in current.children:
                if self._contains_node(child, target):
                    contains_target = True
                    break

            if not contains_target:
                # 当前节点不包含目标节点，可以使用其计算结果
                return self.node_results[id(current)]

        # 根据节点类型构建表达式
        if current.type == ASTNode.TYPE.LITERAL:
            # 字面量节点
            return [current.tokens[0]]

        elif current.type == ASTNode.TYPE.GRP_EXP:
            # 分组表达式
            if len(current.children) == 1:
                # 递归处理子表达式
                inner_expr = self._recursive_replace(
                    current.children[0], target, replacement, expr
                )

                # 如果内部表达式只有一个token，不需要添加括号
                if len(inner_expr) == 1:
                    return inner_expr

                # 添加括号
                l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                return [l_bracket] + inner_expr + [r_bracket]
            else:
                return []

        elif current.type == ASTNode.TYPE.BIN_EXP:
            # 二元表达式
            if len(current.children) == 2:
                # 递归处理左右子表达式
                left_expr = self._recursive_replace(
                    current.children[0], target, replacement, expr
                )

                right_expr = self._recursive_replace(
                    current.children[1], target, replacement, expr
                )

                # 查找操作符
                op_token = None
                for token in current.tokens:
                    if token.type == Token.TYPE.OPERATOR:
                        op_token = token
                        break

                if op_token:
                    # 检查是否需要为左子表达式添加括号
                    left_needs_brackets = self._needs_brackets_for_expression(left_expr, op_token.value, "left")

                    # 检查是否需要为右子表达式添加括号
                    right_needs_brackets = self._needs_brackets_for_expression(right_expr, op_token.value, "right")

                    result = []

                    # 添加左子表达式，必要时添加括号
                    if left_needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        result.extend([l_bracket] + left_expr + [r_bracket])
                    else:
                        result.extend(left_expr)

                    # 添加操作符
                    result.append(op_token)

                    # 添加右子表达式，必要时添加括号
                    if right_needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        result.extend([l_bracket] + right_expr + [r_bracket])
                    else:
                        result.extend(right_expr)

                    return result
                else:
                    return []
            else:
                return []

        elif current.type == ASTNode.TYPE.URY_EXP:
            # 一元表达式
            if len(current.children) == 1:
                # 递归处理子表达式
                expr_result = self._recursive_replace(
                    current.children[0], target, replacement, expr
                )

                # 查找操作符
                op_token = None
                for token in current.tokens:
                    if token.type == Token.TYPE.OPERATOR:
                        op_token = token
                        break

                if op_token:
                    # 检查是否需要为表达式添加括号
                    needs_brackets = self._needs_brackets_for_unary_expr(expr_result)

                    if needs_brackets:
                        l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
                        r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
                        return [op_token, l_bracket] + expr_result + [r_bracket]
                    else:
                        return [op_token] + expr_result
                else:
                    return []
            else:
                return []

        elif current.type == ASTNode.TYPE.FUN_CAL:
            # 函数调用
            func_token = None
            for token in current.tokens:
                if token.type == Token.TYPE.FUNCTION:
                    func_token = token
                    break

            if func_token:
                result = [func_token, Token(Token.TYPE.LBRACKET, "(", [0, 0])]

                # 递归处理所有参数
                for i, child in enumerate(current.children):
                    if i > 0:
                        result.append(Token(Token.TYPE.SEPARATOR, ",", [0, 0]))

                    arg_expr = self._recursive_replace(
                        child, target, replacement, expr
                    )
                    result.extend(arg_expr)

                result.append(Token(Token.TYPE.RBRACKET, ")", [0, 0]))
                return result
            else:
                return []

        # 其他类型节点
        return []

    def _needs_brackets_for_expression(self, expr: list[Token], parent_op: str, position: str) -> bool:
        r"""
        判断表达式是否需要括号
        :param expr: 要判断的表达式
        :param parent_op: 父操作符
        :param position: 表达式位置 ('left' 或 'right')
        :return: 是否需要括号
        """
        # 单个token不需要括号
        if len(expr) == 1:
            return False

        # 如果表达式已经带有括号，不需要再加
        if (expr[0].type == Token.TYPE.LBRACKET and expr[0].value == "(" and
            expr[-1].type == Token.TYPE.RBRACKET and expr[-1].value == ")"):
            return False

        # 如果表达式是函数调用，不需要括号
        if (len(expr) >= 3 and expr[0].type == Token.TYPE.FUNCTION and
            expr[1].type == Token.TYPE.LBRACKET and expr[-1].type == Token.TYPE.RBRACKET):
            return False

        # 查找表达式中的主操作符
        main_op_pos = self._find_main_operator_position(expr)
        if main_op_pos is not None:
            main_op = expr[main_op_pos].value

            # 根据运算符优先级判断
            return self._needs_brackets_by_precedence(main_op, parent_op, position)

        # 默认情况，保守起见添加括号
        return True

    def _needs_brackets_for_unary_expr(self, expr: list[Token]) -> bool:
        r"""
        判断一元表达式的操作数是否需要括号
        :param expr: 要判断的表达式
        :return: 是否需要括号
        """
        # 单个token不需要括号
        if len(expr) == 1:
            return False

        # 如果表达式已经带有括号，不需要再加
        if (expr[0].type == Token.TYPE.LBRACKET and expr[0].value == "(" and
            expr[-1].type == Token.TYPE.RBRACKET and expr[-1].value == ")"):
            return False

        # 如果表达式是函数调用，不需要括号
        if (len(expr) >= 3 and expr[0].type == Token.TYPE.FUNCTION and
            expr[1].type == Token.TYPE.LBRACKET and expr[-1].type == Token.TYPE.RBRACKET):
            return False

        # 查找表达式中的主操作符
        main_op_pos = self._find_main_operator_position(expr)
        if main_op_pos is not None:
            # 二元表达式通常需要括号
            return True

        # 默认情况下不需要括号
        return False

    def _needs_brackets_by_precedence(self, node_op: str, parent_op: str, position: str) -> bool:
        r"""
        根据运算符优先级判断是否需要括号
        :param node_op: 节点的运算符
        :param parent_op: 父节点的运算符
        :param position: 节点在父节点中的位置 ('left' 或 'right')
        :return: 是否需要括号
        """
        # 定义运算符优先级，数字越大优先级越高
        precedence = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
            "^": 3
        }

        # 获取优先级
        node_prec = precedence.get(node_op, 0)
        parent_prec = precedence.get(parent_op, 0)

        # 如果节点运算符优先级低于父节点，需要括号
        if node_prec < parent_prec:
            return True

        # 如果优先级相同，根据结合性和位置判断
        if node_prec == parent_prec:
            # 加减法和乘除法左结合，只有右侧需要括号
            if node_op in ["+", "-"] and parent_op in ["+", "-"] and position == "right" and node_op != parent_op:
                return True

            if node_op in ["*", "/"] and parent_op in ["*", "/"] and position == "right" and node_op != parent_op:
                return True

            # 减法的特殊处理：左侧是减法时右侧需要括号
            if parent_op == "-" and position == "right":
                return True

            # 除法的特殊处理：左侧是除法时右侧需要括号
            if parent_op == "/" and position == "right":
                return True

            # 幂运算右结合，左侧需要括号
            if node_op == "^" and parent_op == "^" and position == "left":
                return True

        return False

    def _contains_node(self, node: ASTNode, target: ASTNode) -> bool:
        r"""
        检查节点是否包含目标节点
        :param node: 要检查的节点
        :param target: 目标节点
        :return: 是否包含
        """
        if node == target:
            return True

        for child in node.children:
            if self._contains_node(child, target):
                return True

        return False

    def _tokens_equal(self, tokens1: list[Token], tokens2: list[Token]) -> bool:
        r"""
        检查两个Token列表是否相等
        :param tokens1: 第一个Token列表
        :param tokens2: 第二个Token列表
        :return: 是否相等
        """
        if len(tokens1) != len(tokens2):
            return False

        for i in range(len(tokens1)):
            if tokens1[i].type != tokens2[i].type or tokens1[i].value != tokens2[i].value:
                return False

        return True

    def _tokens_to_str(self, tokens: list[Token]) -> str:
        r"""
        将Token列表转换为字符串
        :param tokens: Token列表
        :return: 字符串表示
        """
        return ''.join([token.value for token in tokens])

    def execute(self):
        r"""
        执行求值器
        :return: None
        """
        start_time = time.time_ns()
        self._evaluate()
        self.time_cost = time.time_ns() - start_time


class Calculation:
    r"""
    执行计算的静态类
    """

    # 四则运算
    @staticmethod
    def addition(augend: list[Token], addend: list[Token]) -> list[Token]:
        r"""
        计算加法
        :param augend: 被加数
        :param addend: 加数
        :return: 加法运算的结果
        """
        # 1. 特殊情况: 任一操作数为0
        if Calculation.is_zero(augend):
            return addend
        if Calculation.is_zero(addend):
            return augend

        # 2. 处理整数和分数的加法
        if Calculation.is_numeric(augend) and Calculation.is_numeric(addend):
            return Calculation.add_numeric(augend, addend)

        # 3. 处理变量情况

        # 3.1 同类型变量
        if (len(augend) == 1 and len(addend) == 1 and
                augend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                addend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                augend[0].value == addend[0].value):
            # 相同变量相加: x + x = 2*x
            return [
                Token(Token.TYPE.INTEGER, "2", [0, 0]),
                Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                augend[0]
            ]

        # 4. 无法化简的情况，保持原始表达式形式
        result = augend.copy()
        result.append(Token(Token.TYPE.OPERATOR, "+", [0, 0]))
        result.extend(addend)
        return result

    @staticmethod
    def subtraction(minuend: list[Token], subtrahend: list[Token]) -> list[Token]:
        r"""
        计算减法
        :param minuend: 被减数
        :param subtrahend: 减数
        :return: 减法运算的结果
        """
        # 1. 特殊情况: 减数为0
        if Calculation.is_zero(subtrahend):
            return minuend

        # 2. 特殊情况: 被减数为0
        if Calculation.is_zero(minuend):
            return Calculation.negate_expression(subtrahend)

        # 3. 处理整数和分数的减法
        if Calculation.is_numeric(minuend) and Calculation.is_numeric(subtrahend):
            # 转换为加法: a - b = a + (-b)
            negated_subtrahend = Calculation.negate_expression(subtrahend)
            return Calculation.add_numeric(minuend, negated_subtrahend)

        # 4. 处理变量情况

        # 4.1 同类型变量
        if (len(minuend) == 1 and len(subtrahend) == 1 and
                minuend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                subtrahend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                minuend[0].value == subtrahend[0].value):
            # 相同变量相减: x - x = 0
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 5. 无法化简的情况，保持原始表达式形式
        result = minuend.copy()
        result.append(Token(Token.TYPE.OPERATOR, "-", [0, 0]))

        # 如果减数是复杂表达式，需要加括号
        if len(subtrahend) > 1 and not (len(subtrahend) == 3 and subtrahend[1].value == "/"):
            l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
            r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
            result.extend([l_bracket] + subtrahend + [r_bracket])
        else:
            result.extend(subtrahend)

        return result

    @staticmethod
    def multiplication(factor_1: list[Token], factor_2: list[Token]) -> list[Token]:
        r"""
        计算乘法
        :param factor_1: 因数1
        :param factor_2: 因数2
        :return: 乘法运算的结果
        """
        # 1. 特殊情况: 任一因数为0
        if Calculation.is_zero(factor_1) or Calculation.is_zero(factor_2):
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 2. 特殊情况: 任一因数为1
        if Calculation.is_one(factor_1):
            return factor_2
        if Calculation.is_one(factor_2):
            return factor_1

        # 3. 处理整数和分数的乘法
        if Calculation.is_numeric(factor_1) and Calculation.is_numeric(factor_2):
            return Calculation.multiply_numeric(factor_1, factor_2)

        # 4. 处理变量与数值的乘法

        # 4.1 无理数乘法的特殊情况
        if (len(factor_1) == 1 and len(factor_2) == 1 and
                factor_1[0].type == Token.TYPE.NATIVE_IRRATIONAL and factor_2[0].type == Token.TYPE.NATIVE_IRRATIONAL):
            # 处理无理数与无理数的乘法 (如 π*π)
            if factor_1[0].value == "π" and factor_2[0].value == "π":
                # π*π = π^2
                return [
                    factor_1[0],
                    Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                    Token(Token.TYPE.INTEGER, "2", [0, 0])
                ]
            if factor_1[0].value == "𝑒" and factor_2[0].value == "𝑒":
                # e*e = e^2
                return [
                    factor_1[0],
                    Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                    Token(Token.TYPE.INTEGER, "2", [0, 0])
                ]

        # 4.2 数值 * 变量
        if (Calculation.is_numeric(factor_1) and len(factor_2) == 1 and
                factor_2[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            # 整数/分数 * 变量
            return factor_1 + [Token(Token.TYPE.OPERATOR, "*", [0, 0])] + factor_2

        # 4.3 变量 * 数值
        if (Calculation.is_numeric(factor_2) and len(factor_1) == 1 and
                factor_1[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            # 变量 * 整数/分数 (标准化为 整数/分数 * 变量)
            return factor_2 + [Token(Token.TYPE.OPERATOR, "*", [0, 0])] + factor_1

        # 5. 无法化简的情况，保持原始表达式形式
        result = factor_1.copy()
        result.append(Token(Token.TYPE.OPERATOR, "*", [0, 0]))
        result.extend(factor_2)
        return result

    @staticmethod
    def division(dividend: list[Token], divisor: list[Token]) -> list[Token]:
        r"""
        计算除法.结果化至最简形式
        :param dividend: 被除数
        :param divisor: 除数
        :return: 除法运算的结果
        """
        # 1. 错误情况: 除数为0
        if Calculation.is_zero(divisor):
            raise OlocCalculationError(
                OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                "Division by zero",
                [0],  # 位置信息需要更准确
                primary_info="division by zero"
            )

        # 2. 特殊情况: 被除数为0
        if Calculation.is_zero(dividend):
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 3. 特殊情况: 除数为1
        if Calculation.is_one(divisor):
            return dividend

        # 4. 处理整数和分数的除法
        if Calculation.is_numeric(dividend) and Calculation.is_numeric(divisor):
            # 转换为分数
            num_dividend, den_dividend = Calculation.to_fraction(dividend)
            num_divisor, den_divisor = Calculation.to_fraction(divisor)

            # a/b ÷ c/d = (a/b) × (d/c) = (a×d)/(b×c)
            num_result = num_dividend * den_divisor
            den_result = den_dividend * num_divisor

            return Calculation.create_fraction(num_result, den_result)

        # 5. 处理变量与整数/分数的除法
        if (len(dividend) == 1 and
                dividend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                Calculation.is_numeric(divisor)):
            # 变量 / 整数/分数
            if len(divisor) == 1:  # 整数
                # 创建分数形式
                return [
                    dividend[0],
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    divisor[0]
                ]
            else:  # 分数
                # 变量 / (a/b) = (变量 * b) / a
                num = divisor[0].value
                den = divisor[2].value

                # 创建 变量*b 的Token
                var_times_den = [
                    dividend[0],
                    Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                    Token(Token.TYPE.INTEGER, den, [0, 0])
                ]

                # 创建 (变量*b)/a 的Token
                return [
                    Token(Token.TYPE.LBRACKET, "(", [0, 0]),
                ] + var_times_den + [
                    Token(Token.TYPE.RBRACKET, ")", [0, 0]),
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    Token(Token.TYPE.INTEGER, num, [0, 0])
                ]

        # 6. 特殊情况：同类无理数相除
        if (len(dividend) == 1 and len(divisor) == 1 and
                dividend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                divisor[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                dividend[0].value == divisor[0].value):
            # 相同变量相除：x/x = 1
            return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

        # 7. 无法化简的情况，保持原始表达式形式
        # 需要确保复杂表达式加上括号
        if len(dividend) > 1 and not (len(dividend) == 3 and dividend[1].value == "/"):
            dividend_with_brackets = [
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + dividend + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]
        else:
            dividend_with_brackets = dividend.copy()

        if len(divisor) > 1 and not (len(divisor) == 3 and divisor[1].value == "/"):
            divisor_with_brackets = [
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + divisor + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]
        else:
            divisor_with_brackets = divisor.copy()

        return dividend_with_brackets + [Token(Token.TYPE.OPERATOR, "/", [0, 0])] + divisor_with_brackets

    # 辅助方法
    @staticmethod
    def is_zero(tokens: list[Token]) -> bool:
        """
        判断Token列表是否表示0
        :param tokens: 待判断的Token列表
        :return: 是否表示0
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "0":
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "0"):
            return True

        return False

    @staticmethod
    def is_one(tokens: list[Token]) -> bool:
        """
        判断Token列表是否表示1
        :param tokens: 待判断的Token列表
        :return: 是否表示1
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "1":
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == tokens[2].value):
            return True

        return False

    @staticmethod
    def is_numeric(tokens: list[Token]) -> bool:
        """
        判断Token列表是否表示纯数值（整数或分数）
        :param tokens: 待判断的Token列表
        :return: 是否是纯数值
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[2].type == Token.TYPE.INTEGER):
            return True

        return False

    @staticmethod
    def to_fraction(tokens: list[Token]) -> tuple:
        """
        将Token列表转换为分数表示
        :param tokens: 待转换的Token列表
        :return: 分子和分母的元组
        :raises ValueError: 无法转换为分数时
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            return int(tokens[0].value), 1

        if len(tokens) == 3 and tokens[1].value == "/":
            return int(tokens[0].value), int(tokens[2].value)

        raise ValueError(f"Cannot convert to fraction: {tokens}")

    @staticmethod
    def add_numeric(a: list[Token], b: list[Token]) -> list[Token]:
        """
        处理纯数值（整数或分数）的加法
        :param a: 被加数
        :param b: 加数
        :return: 加法结果
        """
        # 转换为分数形式
        num_a, den_a = Calculation.to_fraction(a)
        num_b, den_b = Calculation.to_fraction(b)

        # 计算: a/b + c/d = (a*d + c*b)/(b*d)
        num_result = num_a * den_b + num_b * den_a
        den_result = den_a * den_b

        # 化简
        return Calculation.create_fraction(num_result, den_result)

    @staticmethod
    def multiply_numeric(a: list[Token], b: list[Token]) -> list[Token]:
        """
        处理纯数值（整数或分数）的乘法
        :param a: 因数1
        :param b: 因数2
        :return: 乘法结果
        """
        # 转换为分数形式
        num_a, den_a = Calculation.to_fraction(a)
        num_b, den_b = Calculation.to_fraction(b)

        # 计算: (a/b) * (c/d) = (a*c)/(b*d)
        num_result = num_a * num_b
        den_result = den_a * den_b

        # 化简
        return Calculation.create_fraction(num_result, den_result)

    @staticmethod
    def negate_expression(tokens: list[Token]) -> list[Token]:
        """
        对表达式取反
        :param tokens: 要取反的表达式
        :return: 取反后的表达式
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            # 整数取反
            value = str(-int(tokens[0].value))
            return [Token(Token.TYPE.INTEGER, value, [0, len(value) - 1])]

        if len(tokens) == 3 and tokens[1].value == "/":
            # 分数取反，取反分子
            num = -int(tokens[0].value)
            den = int(tokens[2].value)
            return Calculation.create_fraction(num, den)

        # 复杂表达式，添加负号和括号
        neg_op = Token(Token.TYPE.OPERATOR, "-", [0, 0])
        if len(tokens) > 1:
            # 需要括号
            l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
            r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
            return [neg_op, l_bracket] + tokens + [r_bracket]
        else:
            # 不需要括号
            return [neg_op] + tokens

    @staticmethod
    def get_reciprocal(tokens: list[Token]) -> list[Token]:
        """
        计算倒数
        :param tokens: 待求倒数的Token列表
        :return: 倒数结果
        :raises OlocCalculationError: 当原数为0时
        """
        num, den = Calculation.to_fraction(tokens)

        # 检查分子是否为0
        if num == 0:
            raise OlocCalculationError(
                OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                "Reciprocal of zero",
                [0],
                primary_info="reciprocal of zero"
            )

        # 计算倒数: (a/b)^-1 = b/a
        return Calculation.create_fraction(den, num)

    @staticmethod
    def create_fraction(numerator: int, denominator: int) -> list[Token]:
        """
        创建分数Token列表，自动化简
        :param numerator: 分子
        :param denominator: 分母
        :return: 分数Token列表
        :raises OlocCalculationError: 分母为0时
        """
        # 检查除数是否为0
        if denominator == 0:
            raise OlocCalculationError(
                OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                "Division by zero",
                [0],
                primary_info="denominator is zero"
            )

        # 计算最大公约数进行约分
        from math import gcd
        g = gcd(abs(numerator), abs(denominator))
        numerator //= g
        denominator //= g

        # 处理负号情况
        if denominator < 0:
            numerator, denominator = -numerator, -denominator

        # 创建结果Token
        if denominator == 1:
            # 整数结果
            result_value = str(numerator)
            return [Token(Token.TYPE.INTEGER, result_value, [0, len(result_value) - 1])]
        else:
            # 分数结果
            num_str = str(numerator)
            den_str = str(denominator)

            num_token = Token(Token.TYPE.INTEGER, num_str, [0, len(num_str) - 1])
            op_token = Token(Token.TYPE.OPERATOR, "/", [len(num_str), len(num_str)])
            den_token = Token(Token.TYPE.INTEGER, den_str,
                            [len(num_str) + 1, len(num_str) + len(den_str)])
            return [num_token, op_token, den_token]


class Function:
    r"""
    函数类，提供各种数学函数的实现
    """

    class Pow:
        r"""
        指数函数相关功能
        """

        @staticmethod
        def pow(x: list[Token], y: list[Token]) -> list[Token]:
            r"""
            计算指数函数
            :param x: 底数Token流
            :param y: 次数Token流
            :return: 计算结果
            :raises OlocCalculationError: 当出现0^0情况时
            """
            # 特殊情况: 0^0
            if Calculation.is_zero(x) and Calculation.is_zero(y):
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.ZERO_TO_THE_POWER_OF_ZERO,
                    "Zero to the power of zero",
                    [0],
                    primary_info="0^0 is undefined"
                )

            # 特殊情况: x^0 = 1
            if Calculation.is_zero(y):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 特殊情况: x^1 = x
            if Calculation.is_one(y):
                return x

            # 特殊情况: 0^y = 0 (y不为0)
            if Calculation.is_zero(x):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 特殊情况: 1^y = 1
            if Calculation.is_one(x):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 处理负整数次幂
            if (len(y) == 1 and y[0].type == Token.TYPE.INTEGER and y[0].value.startswith('-')):
                # 负整数幂: x^(-n) = 1/(x^n)
                positive_exponent = [Token(Token.TYPE.INTEGER, y[0].value[1:], [0, 0])]
                positive_result = Function.Pow.pow(x, positive_exponent)

                # 计算倒数
                return Calculation.get_reciprocal(positive_result)

            # 处理整数的整数次幂
            if (len(x) == 1 and x[0].type == Token.TYPE.INTEGER and
                    len(y) == 1 and y[0].type == Token.TYPE.INTEGER):
                base = int(x[0].value)
                exponent = int(y[0].value)

                # 计算整数次幂
                try:
                    result = base ** exponent
                    result_str = str(result)
                    return [Token(Token.TYPE.INTEGER, result_str, [0, len(result_str) - 1])]
                except OverflowError:
                    # 结果太大，保持原始表达式形式
                    pass

            # 处理分数的整数次幂
            if (len(x) == 3 and x[1].value == "/" and
                    len(y) == 1 and y[0].type == Token.TYPE.INTEGER):
                num, den = Calculation.to_fraction(x)
                exponent = int(y[0].value)

                if exponent > 0:
                    # 正整数次幂: (a/b)^n = a^n/b^n
                    try:
                        num_result = num ** exponent
                        den_result = den ** exponent
                        return Calculation.create_fraction(num_result, den_result)
                    except OverflowError:
                        # 结果太大，保持原始表达式形式
                        pass
                elif exponent < 0:
                    # 负整数次幂: (a/b)^(-n) = (b/a)^n
                    exponent = -exponent
                    try:
                        num_result = den ** exponent
                        den_result = num ** exponent
                        return Calculation.create_fraction(num_result, den_result)
                    except OverflowError:
                        # 结果太大，保持原始表达式形式
                        pass

            # 特殊情况: 无理数的简单指数
            if (len(x) == 1 and x[0].type == Token.TYPE.NATIVE_IRRATIONAL and
                    len(y) == 1 and y[0].type == Token.TYPE.INTEGER):
                # 例如 π^2, e^3 等
                return [
                    x[0],
                    Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                    y[0]
                ]

            # 无法直接计算的情况，保持原始表达式形式
            return x + [Token(Token.TYPE.OPERATOR, "^", [0, 0])] + y

        @staticmethod
        def sqrt(x: list[Token]) -> list[Token]:
            r"""
            计算平方根函数
            :param x: 被开方数Token流
            :return: 计算结果
            """
            # 特殊情况: √0 = 0
            if Calculation.is_zero(x):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 特殊情况: √1 = 1
            if Calculation.is_one(x):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 处理完全平方数
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)
                # 检查是否是完全平方数
                sqrt_value = int(value ** 0.5)
                if sqrt_value ** 2 == value:
                    return [Token(Token.TYPE.INTEGER, str(sqrt_value), [0, 0])]

            # 使用幂运算表示: √x = x^(1/2)
            half_power = [
                Token(Token.TYPE.INTEGER, "1", [0, 0]),
                Token(Token.TYPE.OPERATOR, "/", [1, 1]),
                Token(Token.TYPE.INTEGER, "2", [2, 2])
            ]
            return Function.Pow.pow(x, half_power)

        @staticmethod
        def sq(x: list[Token]) -> list[Token]:
            r"""
            计算平方函数
            :param x: 被平方数Token流
            :return: 计算结果
            """
            # 使用幂运算表示: sq(x) = x^2
            square = [Token(Token.TYPE.INTEGER, "2", [0, 0])]
            return Function.Pow.pow(x, square)

        @staticmethod
        def cub(x: list[Token]) -> list[Token]:
            r"""
            计算立方函数
            :param x: 被立方数Token流
            :return: 计算结果
            """
            # 使用幂运算表示: cub(x) = x^3
            cube = [Token(Token.TYPE.INTEGER, "3", [0, 0])]
            return Function.Pow.pow(x, cube)

        @staticmethod
        def rec(x: list[Token]) -> list[Token]:
            r"""
            计算倒数函数
            :param x: 被求倒数Token流
            :return: 计算结果
            """
            # 使用幂运算表示: rec(x) = x^(-1)
            negative_one = [Token(Token.TYPE.INTEGER, "-1", [0, 1])]
            return Function.Pow.pow(x, negative_one)


"""test"""
if __name__ == "__main__":
    from oloc_lexer import Lexer
    from oloc_parser import Parser
    from oloc_preprocessor import Preprocessor

    def test_expression(expr):
        print(f"\nTesting: {expr}")
        try:
            # 预处理
            preprocessor = Preprocessor(expr)
            preprocessor.execute()

            # 词法分析
            lexer = Lexer(preprocessor.expression)
            lexer.execute()

            # 语法分析
            parser = Parser(lexer.tokens)
            parser.execute()

            # 求值
            evaluator = Evaluator(parser.expression, parser.tokens, parser.ast)
            evaluator.execute()

            # 打印结果
            print(f"Result: {evaluator.expression}")
            print("Calculation steps:")
            for i, step in enumerate(evaluator.result):
                step_expr = ' '.join([token.value for token in step])
                print(f"  Step {i}: {step_expr}")

        except Exception as e:
            print(f"Error: {e}")

    # 测试用例1: 基本整数加法
    test_expression("1+2")

    # 测试用例2: 基本整数四则运算
    test_expression("2*3+4")

    # 测试用例3: 带括号的表达式
    test_expression("(2+3)*4")

    # 测试用例4: 分数运算
    test_expression("1/2+3/4")

    # 测试用例5: 带负数的运算
    test_expression("-5+7")

    # 测试用例6: 幂运算
    test_expression("2^3")

    # 测试用例7: 函数调用
    test_expression("sqrt(16)")

    # 测试用例8: 包含无理数的表达式
    test_expression("2*π")

    # 测试用例9: 复杂表达式
    test_expression("(3+4)*(5-2)/sqrt(16)")

    # 测试用例10: 多层嵌套表达式
    test_expression("((2+3)^2-1)/((4*5)+(6/3))")

    # 附加测试用例11: 基本分数运算
    test_expression("3/4*2/3")

    # 附加测试用例12: 负数幂运算
    test_expression("2^(-3)")

    # 附加测试用例13: 带有无理数的复杂运算
    test_expression("π^2+e^2")

    # 附加测试用例14: 函数嵌套
    test_expression("sqrt(sqrt(16))")

    # 附加测试用例15: 复杂分数运算
    test_expression("(1/2+1/3)/(1/4+1/5)")

    # 附加测试用例16: 变量相乘
    test_expression("π*π")

    # 附加测试用例17: 变量相除
    test_expression("x/x")

    # 附加测试用例18: 零值测试
    test_expression("0+5")

    # 附加测试用例19: 单位值测试
    test_expression("1*7")

    # 附加测试用例20: 除零错误测试
    test_expression("5/0")

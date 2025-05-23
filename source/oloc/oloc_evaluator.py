r"""
:author: WaterRun
:date: 2025-05-19
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

import time
import math
from enum import auto
from math import gcd, lcm

from oloc_token import Token
from oloc_ast import ASTTree, ASTNode
from oloc_exceptions import *


class CalculateEvent:
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


class StepManager:
    r"""
    计算步骤管理器，负责生成和优化计算步骤
    """

    def __init__(self):
        self.steps = []
        self.step_expressions = set()

    def add_step(self, tokens: list[Token]) -> bool:
        r"""
        添加计算步骤，避免重复
        :param tokens: 表示当前步骤的Token列表
        :return: 是否成功添加（非重复）
        """
        step_str = ''.join([t.value for t in tokens])
        if step_str in self.step_expressions:
            return False

        self.steps.append(tokens)
        self.step_expressions.add(step_str)
        return True

    def optimize_steps(self) -> list[list[Token]]:
        r"""
        优化计算步骤，移除不必要的步骤
        :return: 优化后的步骤列表
        """
        if len(self.steps) <= 2:  # 原始表达式和最终结果，不需要优化
            return self.steps

        # 移除表达式变化很小的中间步骤
        optimized_steps = [self.steps[0]]  # 保留原始表达式

        # 对中间步骤进行选择
        for i in range(1, len(self.steps) - 1):
            # 检查当前步骤是否与前一步骤有显著差异
            if self._significant_difference(self.steps[i], optimized_steps[-1]):
                optimized_steps.append(self.steps[i])

        # 确保包含最终结果
        if optimized_steps[-1] != self.steps[-1]:
            optimized_steps.append(self.steps[-1])

        return optimized_steps

    def _significant_difference(self, step1: list[Token], step2: list[Token]) -> bool:
        r"""
        判断两个步骤之间是否有显著差异
        :param step1: 第一个步骤的Token列表
        :param step2: 第二个步骤的Token列表
        :return: 是否有显著差异
        """
        # 如果Token数量差异超过某个阈值，认为有显著差异
        if abs(len(step1) - len(step2)) > 3:
            return True

        # 计算不同Token的数量
        diff_count = 0
        min_len = min(len(step1), len(step2))

        for i in range(min_len):
            if step1[i].type != step2[i].type or step1[i].value != step2[i].value:
                diff_count += 1

                # 如果差异超过阈值，认为有显著差异
                if diff_count > 2:
                    return True

        # 考虑长度差异导致的额外Token
        diff_count += abs(len(step1) - len(step2))

        return diff_count > 2


class NodeEvaluator:
    r"""
    节点求值策略的基类
    """
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        r"""
        评估节点
        :param node: 要评估的节点
        :param evaluator: 求值器实例
        :return: 计算结果的Token列表
        """
        raise NotImplementedError("Node evaluators must implement evaluate method")


class LiteralEvaluator(NodeEvaluator):
    r"""字面量节点求值策略"""
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        return [node.tokens[0]]


class GroupExpressionEvaluator(NodeEvaluator):
    r"""分组表达式节点求值策略"""
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        if len(node.children) != 1:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                evaluator.expression,
                [node.tokens[0].range[0] if node.tokens else 0],
                primary_info=f"Group expression should have exactly one child, got {len(node.children)}"
            )

        # 计算括号内的表达式
        inner_result = evaluator._evaluate_node(node.children[0])

        # 直接返回内部结果，必要时由上层方法添加括号
        return inner_result


class BinaryExpressionEvaluator(NodeEvaluator):
    r"""二元表达式节点求值策略"""
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        if len(node.children) != 2:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                evaluator.expression,
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
                evaluator.expression,
                [0],
                primary_info="Binary expression missing operator"
            )

        # 计算左右子表达式
        left_result = evaluator._evaluate_node(node.children[0])
        right_result = evaluator._evaluate_node(node.children[1])

        # 根据操作符执行计算
        operator = op_token.value

        if operator == "+":
            return Calculation.addition(left_result, right_result)
        elif operator == "-":
            return Calculation.subtraction(left_result, right_result)
        elif operator == "*":
            return Calculation.multiplication(left_result, right_result)
        elif operator == "/":
            return Calculation.division(left_result, right_result)
        elif operator == "^":
            return Function.Pow.pow(left_result, right_result)
        elif operator == "%":
            return Function.Other.mod(left_result, right_result)
        else:
            raise OlocCalculationError(
                OlocCalculationError.TYPE.UNSUPPORTED_OPERATOR,
                evaluator.expression,
                [op_token.range[0]],
                primary_info=f"Unsupported operator: {operator}"
            )


class UnaryExpressionEvaluator(NodeEvaluator):
    r"""一元表达式节点求值策略"""
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        if len(node.children) != 1:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                evaluator.expression,
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
                evaluator.expression,
                [0],
                primary_info="Unary expression missing operator"
            )

        # 计算操作数
        operand_result = evaluator._evaluate_node(node.children[0])

        # 应用一元运算符
        operator = op_token.value

        if operator == "-":
            return Calculation.negate_expression(operand_result)
        elif operator == "+":
            return operand_result  # 正号不改变值
        elif operator == "√":
            return Function.Pow.sqrt(operand_result)
        elif operator == "|":
            return Function.Other.abs(operand_result)
        elif operator == "!":
            return Function.Other.fact(operand_result)
        elif operator == "°":
            return Function.Trig.degrees_to_radians(operand_result)
        else:
            raise OlocCalculationError(
                OlocCalculationError.TYPE.UNSUPPORTED_OPERATOR,
                evaluator.expression,
                [op_token.range[0]],
                primary_info=f"Unsupported unary operator: {operator}"
            )


class FunctionCallEvaluator(NodeEvaluator):
    r"""函数调用节点求值策略"""
    @staticmethod
    def evaluate(node: ASTNode, evaluator) -> list[Token]:
        # 获取函数名
        func_token = None
        for token in node.tokens:
            if token.type == Token.TYPE.FUNCTION:
                func_token = token
                break

        if func_token is None:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                evaluator.expression,
                [0],
                primary_info="Function call missing function name"
            )

        func_name = func_token.value.lower()  # 使用小写进行统一

        # 计算所有参数
        args_results = []
        for child in node.children:
            arg_result = evaluator._evaluate_node(child)
            args_results.append(arg_result)

        # 构建函数映射
        function_map = {
            # 幂函数
            "pow": (Function.Pow.pow, 2),
            "sqrt": (Function.Pow.sqrt, 1),
            "sq": (Function.Pow.sq, 1),
            "cub": (Function.Pow.cub, 1),
            "rec": (Function.Pow.rec, 1),

            # 三角函数
            "sin": (Function.Trig.sin, 1),
            "cos": (Function.Trig.cos, 1),
            "tan": (Function.Trig.tan, 1),
            "csc": (Function.Trig.csc, 1),
            "sec": (Function.Trig.sec, 1),
            "cot": (Function.Trig.cot, 1),
            "asin": (Function.Trig.asin, 1),
            "acos": (Function.Trig.acos, 1),
            "atan": (Function.Trig.atan, 1),
            "rad": (Function.Trig.degrees_to_radians, 1),

            # 对数函数
            "log": (Function.Log.log, 2),
            "ln": (Function.Log.ln, 1),
            "lg": (Function.Log.lg, 1),

            # 其他函数
            "abs": (Function.Other.abs, 1),
            "fact": (Function.Other.fact, 1),
            "gcd": (Function.Other.gcd, 2),
            "lcm": (Function.Other.lcm, 2),
            "mod": (Function.Other.mod, 2),
            "sign": (Function.Other.sign, 1),
            "exp": (Function.Log.exp, 1)
        }

        # 检查函数是否支持
        if func_name not in function_map:
            raise OlocCalculationError(
                exception_type=OlocCalculationError.TYPE.UNSUPPORTED_FUNCTION,
                expression=evaluator.expression,
                positions=[func_token.range[0]],
                primary_info=func_name
            )

        # 获取函数和预期参数数量
        func, expected_args = function_map[func_name]

        # 检查参数数量
        if len(args_results) != expected_args:
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                expression=evaluator.expression,
                positions=[func_token.range[0]],
                primary_info=func_name,
                secondary_info=f"expected {expected_args} argument{'s' if expected_args != 1 else ''}"
            )

        # 调用函数
        return func(*args_results)


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

        # 初始化计算状态记录
        self.calculation_events = []  # 记录计算事件
        self.node_results = {}  # 记录节点计算结果，键为节点ID，值为Token列表
        self.node_original = {}  # 记录节点原始表示，键为节点ID，值为Token列表
        self.eval_order = []  # 记录节点的计算顺序，存储节点ID

        # 初始化步骤管理器
        self.step_manager = StepManager()

        # 记录特殊值表
        self._init_special_values()

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

    def _init_special_values(self):
        r"""
        初始化特殊值表，用于三角函数等特殊角度值计算
        """
        # 特殊角度的三角函数值 (以弧度为单位)
        self.special_angles = {
            # key: 角度值（弧度），value: (sin, cos, tan)
            0: (0, 1, 0),
            math.pi/6: (1/2, math.sqrt(3)/2, 1/math.sqrt(3)),
            math.pi/4: (math.sqrt(2)/2, math.sqrt(2)/2, 1),
            math.pi/3: (math.sqrt(3)/2, 1/2, math.sqrt(3)),
            math.pi/2: (1, 0, float('inf')),
            2*math.pi/3: (math.sqrt(3)/2, -1/2, -math.sqrt(3)),
            3*math.pi/4: (math.sqrt(2)/2, -math.sqrt(2)/2, -1),
            5*math.pi/6: (1/2, -math.sqrt(3)/2, -1/math.sqrt(3)),
            math.pi: (0, -1, 0),
            7*math.pi/6: (-1/2, -math.sqrt(3)/2, 1/math.sqrt(3)),
            5*math.pi/4: (-math.sqrt(2)/2, -math.sqrt(2)/2, 1),
            4*math.pi/3: (-math.sqrt(3)/2, -1/2, math.sqrt(3)),
            3*math.pi/2: (-1, 0, float('inf')),
            5*math.pi/3: (-math.sqrt(3)/2, 1/2, -math.sqrt(3)),
            7*math.pi/4: (-math.sqrt(2)/2, math.sqrt(2)/2, -1),
            11*math.pi/6: (-1/2, math.sqrt(3)/2, -1/math.sqrt(3)),
            2*math.pi: (0, 1, 0)
        }

    def execute(self):
        r"""
        执行求值器
        :return: None
        """
        start_time = time.time_ns()
        self._evaluate()
        self.time_cost = time.time_ns() - start_time

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
        self.step_manager.add_step(self.tokens.copy())

        # 递归求值AST树
        final_result = self._evaluate_node(self.ast.root)

        # 构建结果步骤列表
        self._generate_calculation_steps()

        # 优化步骤
        self.result = self.step_manager.optimize_steps()

        # 更新表达式字符串和tokens
        self.tokens = final_result
        self.expression = ''.join([t.value for t in final_result])

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
            CalculateEvent(CalculateEvent.Type.NODE_EVAL_START, node, None)
        )

        # 根据节点类型选择相应的求值策略
        evaluator = self._get_evaluator_for_node(node)
        result = evaluator.evaluate(node, self)

        # 记录节点计算结果
        self.node_results[id(node)] = result

        # 记录节点完成计算的事件
        self.calculation_events.append(
            CalculateEvent(CalculateEvent.Type.NODE_EVAL_COMPLETE, node, result)
        )

        # 将节点ID添加到计算顺序列表
        self.eval_order.append(id(node))

        # 记录完成一个有意义的计算步骤
        self._record_calculation_step(node)

        return result

    def _get_evaluator_for_node(self, node: ASTNode) -> NodeEvaluator:
        r"""
        根据节点类型获取相应的求值策略
        :param node: 要求值的节点
        :return: 对应的求值策略
        """
        if node.type == ASTNode.TYPE.LITERAL:
            return LiteralEvaluator
        elif node.type == ASTNode.TYPE.GRP_EXP:
            return GroupExpressionEvaluator
        elif node.type == ASTNode.TYPE.BIN_EXP:
            return BinaryExpressionEvaluator
        elif node.type == ASTNode.TYPE.URY_EXP:
            return UnaryExpressionEvaluator
        elif node.type == ASTNode.TYPE.FUN_CAL:
            return FunctionCallEvaluator
        else:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                self.expression,
                [0],
                primary_info=f"Unknown node type: {node.type}"
            )

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
                        result.append(Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0]))
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
            "^": 3,
            "%": 2  # 取余与乘除法同级
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

            if node_op in ["*", "/", "%"] and parent_op in ["*", "/",
                                                            "%"] and position == "right" and node_op != parent_op:
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
            "^": 3,
            "%": 2  # 取余与乘除法同级
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
            CalculateEvent(CalculateEvent.Type.STEP_COMPLETE, node, result)
        )

    def _generate_calculation_steps(self):
        r"""
        根据计算事件生成计算步骤
        """
        # 获取所有步骤完成事件
        step_events = [event for event in self.calculation_events
                       if event.type == CalculateEvent.Type.STEP_COMPLETE]

        # 按照计算的顺序排序步骤
        step_events.sort(key=lambda e: self.eval_order.index(id(e.node)))

        # 为嵌套函数和表达式处理特殊情况
        processed_steps = self._process_nested_steps(step_events)

        # 生成每一步的表达式
        for step_event in processed_steps:
            node = step_event.node
            result = step_event.result

            # 生成该步骤的完整表达式
            step_expr = self._generate_step_expression(node, result)

            # 简化表达式中不必要的括号
            step_expr = self._simplify_expression(step_expr)

            # 添加到步骤管理器
            self.step_manager.add_step(step_expr)

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

        if tokens[0].type != Token.TYPE.LBRACKET or tokens[0].value != "(" or tokens[-1].type != Token.TYPE.RBRACKET or \
                tokens[-1].value != ")":
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
                        sub_expr = tokens[start_pos:j + 1]
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

    def _process_nested_steps(self, step_events: list[CalculateEvent]) -> list[CalculateEvent]:
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
                                CalculateEvent(
                                    CalculateEvent.Type.STEP_COMPLETE,
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
                result.append(Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0]))

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
                        result.append(Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0]))

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

        # 3.1 同类型变量: x + x = 2*x
        if (len(augend) == 1 and len(addend) == 1 and
                augend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                addend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                augend[0].value == addend[0].value):
            return [
                Token(Token.TYPE.INTEGER, "2", [0, 0]),
                Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                augend[0]
            ]

        # 3.2 系数与变量相加: a*x + b*x = (a+b)*x
        if (Calculation._is_coefficient_variable(augend) and
                Calculation._is_coefficient_variable(addend) and
                Calculation._get_variable(augend).value == Calculation._get_variable(addend).value):
            coef1 = Calculation._get_coefficient(augend)
            coef2 = Calculation._get_coefficient(addend)
            variable = Calculation._get_variable(augend)

            # 计算系数和
            coef_sum = Calculation.add_numeric(coef1, coef2)

            # 如果系数和为0，直接返回0
            if Calculation.is_zero(coef_sum):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 如果系数和为1，只返回变量
            if Calculation.is_one(coef_sum):
                return [variable]

            # 否则返回 (a+b)*x
            return coef_sum + [
                Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                variable
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

        # 4.1 同类型变量: x - x = 0
        if (len(minuend) == 1 and len(subtrahend) == 1 and
                minuend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                subtrahend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM,
                                       Token.TYPE.NATIVE_IRRATIONAL] and
                minuend[0].value == subtrahend[0].value):
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 4.2 系数与变量相减: a*x - b*x = (a-b)*x
        if (Calculation._is_coefficient_variable(minuend) and
                Calculation._is_coefficient_variable(subtrahend) and
                Calculation._get_variable(minuend).value == Calculation._get_variable(subtrahend).value):
            coef1 = Calculation._get_coefficient(minuend)
            coef2 = Calculation._get_coefficient(subtrahend)
            variable = Calculation._get_variable(minuend)

            # 计算系数差
            coef_diff = Calculation.subtraction(coef1, coef2)

            # 如果系数差为0，直接返回0
            if Calculation.is_zero(coef_diff):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 如果系数差为1，只返回变量
            if Calculation.is_one(coef_diff):
                return [variable]

            # 如果系数差为-1，返回-x
            if len(coef_diff) == 1 and coef_diff[0].value == "-1":
                return [
                    Token(Token.TYPE.OPERATOR, "-", [0, 0]),
                    variable
                ]

            # 否则返回 (a-b)*x
            return coef_diff + [
                Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                variable
            ]

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

        # 4.1 无理数乘法的特殊情况: π*π = π^2, e*e = e^2
        if (len(factor_1) == 1 and len(factor_2) == 1 and
                factor_1[0].type == Token.TYPE.NATIVE_IRRATIONAL and factor_2[0].type == Token.TYPE.NATIVE_IRRATIONAL):
            if factor_1[0].value == factor_2[0].value:
                return [
                    factor_1[0],
                    Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                    Token(Token.TYPE.INTEGER, "2", [0, 0])
                ]

        # 4.2 同类变量幂的乘法: x^a * x^b = x^(a+b)
        if (Calculation._is_variable_power(factor_1) and
                Calculation._is_variable_power(factor_2) and
                Calculation._get_power_base(factor_1).value == Calculation._get_power_base(factor_2).value):
            base = Calculation._get_power_base(factor_1)
            exp1 = Calculation._get_power_exponent(factor_1)
            exp2 = Calculation._get_power_exponent(factor_2)

            # 计算指数和
            sum_exp = Calculation.addition(exp1, exp2)

            # 如果指数和为0，返回1
            if Calculation.is_zero(sum_exp):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 如果指数和为1，只返回底数
            if Calculation.is_one(sum_exp):
                return [base]

            # 否则返回 x^(a+b)
            return [
                base,
                Token(Token.TYPE.OPERATOR, "^", [0, 0])
            ] + (sum_exp if len(sum_exp) == 1 else [
                                                       Token(Token.TYPE.LBRACKET, "(", [0, 0])
                                                   ] + sum_exp + [
                                                       Token(Token.TYPE.RBRACKET, ")", [0, 0])
                                                   ])

        # 4.3 数值 * 变量: 标准化为数值*变量形式
        if (Calculation.is_numeric(factor_1) and len(factor_2) == 1 and
                factor_2[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return factor_1 + [Token(Token.TYPE.OPERATOR, "*", [0, 0])] + factor_2

        # 4.4 变量 * 数值: 标准化为数值*变量形式
        if (Calculation.is_numeric(factor_2) and len(factor_1) == 1 and
                factor_1[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return factor_2 + [Token(Token.TYPE.OPERATOR, "*", [0, 0])] + factor_1

        # 4.5 系数变量相乘: (a*x) * (b*y) = (a*b)*(x*y)
        if (Calculation._is_coefficient_variable(factor_1) and
                Calculation._is_coefficient_variable(factor_2)):
            coef1 = Calculation._get_coefficient(factor_1)
            coef2 = Calculation._get_coefficient(factor_2)
            var1 = Calculation._get_variable(factor_1)
            var2 = Calculation._get_variable(factor_2)

            # 计算系数积
            coef_product = Calculation.multiply_numeric(coef1, coef2)

            # 如果是同一个变量: a*x * b*x = (a*b)*x^2
            if var1.value == var2.value:
                if Calculation.is_one(coef_product):
                    return [
                        var1,
                        Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                        Token(Token.TYPE.INTEGER, "2", [0, 0])
                    ]
                else:
                    return coef_product + [
                        Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                        var1,
                        Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                        Token(Token.TYPE.INTEGER, "2", [0, 0])
                    ]

            # 对于不同变量: a*x * b*y = (a*b)*(x*y)
            if Calculation.is_one(coef_product):
                return [var1, Token(Token.TYPE.OPERATOR, "*", [0, 0]), var2]
            else:
                return coef_product + [
                    Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                    var1,
                    Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                    var2
                ]

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
                [0],
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

        # 6. 处理幂与除法的关系: x^a / x^b = x^(a-b)
        if (Calculation._is_variable_power(dividend) and
                Calculation._is_variable_power(divisor) and
                Calculation._get_power_base(dividend).value == Calculation._get_power_base(divisor).value):
            base = Calculation._get_power_base(dividend)
            exp1 = Calculation._get_power_exponent(dividend)
            exp2 = Calculation._get_power_exponent(divisor)

            # 计算指数差
            diff_exp = Calculation.subtraction(exp1, exp2)

            # 如果指数差为0，返回1
            if Calculation.is_zero(diff_exp):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 如果指数差为1，只返回底数
            if Calculation.is_one(diff_exp):
                return [base]

            # 如果指数差为负数，可能需要取倒数
            if len(diff_exp) == 1 and diff_exp[0].value.startswith('-'):
                # 负指数: x^(-n) = 1/(x^n)
                pos_exp = [Token(Token.TYPE.INTEGER, diff_exp[0].value[1:], [0, 0])]
                return [
                    Token(Token.TYPE.INTEGER, "1", [0, 0]),
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    Token(Token.TYPE.LBRACKET, "(", [0, 0]),
                    base,
                    Token(Token.TYPE.OPERATOR, "^", [0, 0])
                ] + pos_exp + [
                    Token(Token.TYPE.RBRACKET, ")", [0, 0])
                ]

            # 否则返回 x^(a-b)
            return [
                base,
                Token(Token.TYPE.OPERATOR, "^", [0, 0])
            ] + (diff_exp if len(diff_exp) == 1 else [
                                                         Token(Token.TYPE.LBRACKET, "(", [0, 0])
                                                     ] + diff_exp + [
                                                         Token(Token.TYPE.RBRACKET, ")", [0, 0])
                                                     ])

        # 7. 特殊情况：同类无理数相除: x/x = 1
        if (len(dividend) == 1 and len(divisor) == 1 and
                dividend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                divisor[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                dividend[0].value == divisor[0].value):
            return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

        # 8. 系数变量相除: (a*x) / (b*y)
        if (Calculation._is_coefficient_variable(dividend) and
                Calculation._is_coefficient_variable(divisor)):
            coef1 = Calculation._get_coefficient(dividend)
            coef2 = Calculation._get_coefficient(divisor)
            var1 = Calculation._get_variable(dividend)
            var2 = Calculation._get_variable(divisor)

            # 计算系数商
            coef_quotient = Calculation.division(coef1, coef2)

            # 如果是同一个变量: a*x / b*x = a/b
            if var1.value == var2.value:
                return coef_quotient

            # 对于不同变量: a*x / b*y = (a/b)*(x/y)
            if Calculation.is_one(coef_quotient):
                return [var1, Token(Token.TYPE.OPERATOR, "/", [0, 0]), var2]
            else:
                # 为复杂系数添加括号
                if len(coef_quotient) > 1:
                    coef_quotient = [
                                        Token(Token.TYPE.LBRACKET, "(", [0, 0])
                                    ] + coef_quotient + [
                                        Token(Token.TYPE.RBRACKET, ")", [0, 0])
                                    ]

                return coef_quotient + [
                    Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                    Token(Token.TYPE.LBRACKET, "(", [0, 0]),
                    var1,
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    var2,
                    Token(Token.TYPE.RBRACKET, ")", [0, 0])
                ]

        # 9. 无法化简的情况，保持原始表达式形式
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
                tokens[0].type == Token.TYPE.INTEGER and tokens[2].type == Token.TYPE.INTEGER and
                tokens[0].value == tokens[2].value):
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
        # 处理复杂表达式
        if not Calculation.is_numeric(tokens):
            # 如果不是简单数值，使用1除以该表达式
            return Calculation.division(
                [Token(Token.TYPE.INTEGER, "1", [0, 0])],
                tokens
            )

        # 处理数值
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

    @staticmethod
    def _is_coefficient_variable(tokens: list[Token]) -> bool:
        """
        判断Token列表是否表示系数乘以变量的形式（如2*x）
        :param tokens: 待判断的Token列表
        :return: 是否是系数乘以变量形式
        """
        # 单个变量可以看作1*变量
        if (len(tokens) == 1 and
                tokens[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return True

        # 检查 num * var 形式
        if (len(tokens) == 3 and tokens[1].value == "*" and
                Calculation.is_numeric([tokens[0]]) and
                tokens[2].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return True

        return False

    @staticmethod
    def _get_coefficient(tokens: list[Token]) -> list[Token]:
        """
        获取系数乘以变量形式中的系数部分
        :param tokens: 系数乘以变量形式的Token列表
        :return: 系数部分的Token列表
        """
        if len(tokens) == 1:
            # 单个变量，系数为1
            return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

        # 通常形式 a*x，返回系数a
        return [tokens[0]]

    @staticmethod
    def _get_variable(tokens: list[Token]) -> Token:
        """
        获取系数乘以变量形式中的变量部分
        :param tokens: 系数乘以变量形式的Token列表
        :return: 变量部分的Token
        """
        if len(tokens) == 1:
            # 单个变量
            return tokens[0]

        # 通常形式 a*x，返回变量x
        return tokens[2]

    @staticmethod
    def _is_variable_power(tokens: list[Token]) -> bool:
        """
        判断Token列表是否表示变量的幂形式（如x^2）
        :param tokens: 待判断的Token列表
        :return: 是否是变量的幂形式
        """
        # 单个变量可以看作变量的一次幂
        if (len(tokens) == 1 and
                tokens[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return True

        # 检查 var^num 形式
        if (len(tokens) == 3 and tokens[1].value == "^" and
                tokens[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                Calculation.is_numeric([tokens[2]])):
            return True

        # 检查 var^(expr) 形式
        if (len(tokens) >= 5 and tokens[1].value == "^" and tokens[2].value == "(" and tokens[-1].value == ")" and
                tokens[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            return True

        return False

    @staticmethod
    def _get_power_base(tokens: list[Token]) -> Token:
        """
        获取变量的幂形式中的底数（变量）部分
        :param tokens: 变量的幂形式的Token列表
        :return: 底数部分的Token
        """
        # 返回变量
        return tokens[0]

    @staticmethod
    def _get_power_exponent(tokens: list[Token]) -> list[Token]:
        """
        获取变量的幂形式中的指数部分
        :param tokens: 变量的幂形式的Token列表
        :return: 指数部分的Token列表
        """
        if len(tokens) == 1:
            # 单个变量，指数为1
            return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

        if len(tokens) == 3:
            # 形式 x^2，返回指数2
            return [tokens[2]]

        # 形式 x^(expr)，返回括号内表达式
        return tokens[3:-1]


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

            # 特殊情况: e^(ln(x)) = x
            if (len(x) == 1 and x[0].type == Token.TYPE.NATIVE_IRRATIONAL and x[0].value == "𝑒" and
                    len(y) >= 5 and y[0].value == "ln" and y[1].value == "(" and y[-1].value == ")"):
                # 提取ln()中的参数
                ln_arg = y[2:-1]
                return ln_arg

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

            # 处理整数的分数次幂（开方）
            if (len(x) == 1 and x[0].type == Token.TYPE.INTEGER and
                    len(y) == 3 and y[1].value == "/" and
                    y[0].value == "1" and y[2].type == Token.TYPE.INTEGER):

                base = int(x[0].value)
                root = int(y[2].value)

                # 检查完全幂
                result_value = round(base ** (1 / root), 10)
                if result_value.is_integer():
                    result_str = str(int(result_value))
                    return [Token(Token.TYPE.INTEGER, result_str, [0, len(result_str) - 1])]

            # 特殊情况: 处理无理数的幂运算
            # 对于幂次叠加：(x^a)^b = x^(a*b)
            if Calculation._is_variable_power(x) and Calculation.is_numeric(y):
                base = Calculation._get_power_base(x)
                exp1 = Calculation._get_power_exponent(x)

                # 计算复合指数
                composite_exp = Calculation.multiplication(exp1, y)

                # 如果复合指数为1，只返回底数
                if Calculation.is_one(composite_exp):
                    return [base]

                # 否则返回 base^(composite_exp)
                if len(composite_exp) == 1:
                    return [
                        base,
                        Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                        composite_exp[0]
                    ]
                else:
                    return [
                        base,
                        Token(Token.TYPE.OPERATOR, "^", [0, 0]),
                        Token(Token.TYPE.LBRACKET, "(", [0, 0])
                    ] + composite_exp + [
                        Token(Token.TYPE.RBRACKET, ")", [0, 0])
                    ]

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
                sqrt_value = round(math.sqrt(value), 10)
                if sqrt_value.is_integer():
                    result_str = str(int(sqrt_value))
                    return [Token(Token.TYPE.INTEGER, result_str, [0, len(result_str) - 1])]

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

    class Trig:
        r"""
        三角函数相关功能
        """

        @staticmethod
        def sin(x: list[Token]) -> list[Token]:
            r"""
            计算正弦函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 特殊情况：特殊角度值
            special_angles = {
                "0": "0",
                "π/6": "1/2",
                "π/4": "1/√2",
                "π/3": "√3/2",
                "π/2": "1",
                "2π/3": "√3/2",
                "3π/4": "1/√2",
                "5π/6": "1/2",
                "π": "0",
                "7π/6": "-1/2",
                "5π/4": "-1/√2",
                "4π/3": "-√3/2",
                "3π/2": "-1",
                "5π/3": "-√3/2",
                "7π/4": "-1/√2",
                "11π/6": "-1/2",
                "2π": "0"
            }

            # 检查是否是特殊角度
            angle_str = Function.Trig._get_angle_string(x)
            if angle_str in special_angles:
                result_str = special_angles[angle_str]
                return Function.Trig._parse_special_value(result_str)

            # 处理整数角度
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                # 计算角度对应的特殊值
                angle = int(x[0].value) % 360  # 角度制
                if angle in [0, 180, 360]:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]
                elif angle == 90:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]
                elif angle == 270:
                    return [Token(Token.TYPE.INTEGER, "-1", [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "sin", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def cos(x: list[Token]) -> list[Token]:
            r"""
            计算余弦函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 特殊情况：特殊角度值
            special_angles = {
                "0": "1",
                "π/6": "√3/2",
                "π/4": "1/√2",
                "π/3": "1/2",
                "π/2": "0",
                "2π/3": "-1/2",
                "3π/4": "-1/√2",
                "5π/6": "-√3/2",
                "π": "-1",
                "7π/6": "-√3/2",
                "5π/4": "-1/√2",
                "4π/3": "-1/2",
                "3π/2": "0",
                "5π/3": "1/2",
                "7π/4": "1/√2",
                "11π/6": "√3/2",
                "2π": "1"
            }

            # 检查是否是特殊角度
            angle_str = Function.Trig._get_angle_string(x)
            if angle_str in special_angles:
                result_str = special_angles[angle_str]
                return Function.Trig._parse_special_value(result_str)

            # 处理整数角度
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                # 计算角度对应的特殊值
                angle = int(x[0].value) % 360  # 角度制
                if angle in [90, 270]:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]
                elif angle in [0, 360]:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]
                elif angle == 180:
                    return [Token(Token.TYPE.INTEGER, "-1", [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "cos", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def tan(x: list[Token]) -> list[Token]:
            r"""
            计算正切函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 特殊情况：特殊角度值
            special_angles = {
                "0": "0",
                "π/6": "1/√3",
                "π/4": "1",
                "π/3": "√3",
                "2π/3": "-√3",
                "3π/4": "-1",
                "5π/6": "-1/√3",
                "π": "0",
                "7π/6": "1/√3",
                "5π/4": "1",
                "4π/3": "√3",
                "5π/3": "-√3",
                "7π/4": "-1",
                "11π/6": "-1/√3",
                "2π": "0"
            }

            # 检查是否是π/2或3π/2等不可计算的角度
            angle_str = Function.Trig._get_angle_string(x)
            if angle_str in ["π/2", "3π/2"]:
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DOMAIN_ERROR,
                    "Tangent is undefined",
                    [0],
                    primary_info=f"tan({angle_str}) is undefined"
                )

            # 检查是否是特殊角度
            if angle_str in special_angles:
                result_str = special_angles[angle_str]
                return Function.Trig._parse_special_value(result_str)

            # 处理整数角度
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                # 计算角度对应的特殊值
                angle = int(x[0].value) % 360  # 角度制
                if angle in [0, 180, 360]:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]
                elif angle in [90, 270]:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DOMAIN_ERROR,
                        "Tangent is undefined",
                        [0],
                        primary_info=f"tan({angle}°) is undefined"
                    )
                elif angle == 45:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]
                elif angle == 225:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "tan", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def csc(x: list[Token]) -> list[Token]:
            r"""
            计算余割函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 计算正弦函数的结果
            sin_result = Function.Trig.sin(x)

            # 余割是正弦的倒数: csc(x) = 1/sin(x)
            return Calculation.get_reciprocal(sin_result)

        @staticmethod
        def sec(x: list[Token]) -> list[Token]:
            r"""
            计算正割函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 计算余弦函数的结果
            cos_result = Function.Trig.cos(x)

            # 正割是余弦的倒数: sec(x) = 1/cos(x)
            return Calculation.get_reciprocal(cos_result)

        @staticmethod
        def cot(x: list[Token]) -> list[Token]:
            r"""
            计算余切函数
            :param x: 角度Token流
            :return: 计算结果
            """
            # 特殊情况：特殊角度值
            special_angles = {
                "π/6": "√3",
                "π/4": "1",
                "π/3": "1/√3",
                "2π/3": "-1/√3",
                "3π/4": "-1",
                "5π/6": "-√3",
                "7π/6": "√3",
                "5π/4": "1",
                "4π/3": "1/√3",
                "5π/3": "-1/√3",
                "7π/4": "-1",
                "11π/6": "-√3"
            }

            # 检查是否是0或π等不可计算的角度
            angle_str = Function.Trig._get_angle_string(x)
            if angle_str in ["0", "π", "2π"]:
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DOMAIN_ERROR,
                    "Cotangent is undefined",
                    [0],
                    primary_info=f"cot({angle_str}) is undefined"
                )

            # 检查是否是特殊角度
            if angle_str in special_angles:
                result_str = special_angles[angle_str]
                return Function.Trig._parse_special_value(result_str)

            # 计算正切函数的结果
            tan_result = Function.Trig.tan(x)

            # 余切是正切的倒数: cot(x) = 1/tan(x)
            return Calculation.get_reciprocal(tan_result)

        @staticmethod
        def asin(x: list[Token]) -> list[Token]:
            r"""
            计算反正弦函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 特殊情况：常见值
            special_values = {
                "0": "0",
                "1/2": "π/6",
                "√3/2": "π/3",
                "1": "π/2",
                "-1/2": "-π/6",
                "-√3/2": "-π/3",
                "-1": "-π/2"
            }

            # 检查是否是特殊值
            value_str = Function.Trig._get_value_string(x)
            if value_str in special_values:
                return Function.Trig._parse_special_value(special_values[value_str])

            # 检查是否在定义域内: -1 ≤ x ≤ 1
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)
                if value > 1 or value < -1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DOMAIN_ERROR,
                        "Arcsine domain error",
                        [0],
                        primary_info=f"asin({value}) is undefined: input must be in range [-1, 1]"
                    )

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "asin", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def acos(x: list[Token]) -> list[Token]:
            r"""
            计算反余弦函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 特殊情况：常见值
            special_values = {
                "0": "π/2",
                "1/2": "π/3",
                "√3/2": "π/6",
                "1": "0",
                "-1/2": "2π/3",
                "-√3/2": "5π/6",
                "-1": "π"
            }

            # 检查是否是特殊值
            value_str = Function.Trig._get_value_string(x)
            if value_str in special_values:
                return Function.Trig._parse_special_value(special_values[value_str])

            # 检查是否在定义域内: -1 ≤ x ≤ 1
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)
                if value > 1 or value < -1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DOMAIN_ERROR,
                        "Arccosine domain error",
                        [0],
                        primary_info=f"acos({value}) is undefined: input must be in range [-1, 1]"
                    )

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "acos", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def atan(x: list[Token]) -> list[Token]:
            r"""
            计算反正切函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 特殊情况：常见值
            special_values = {
                "0": "0",
                "1/√3": "π/6",
                "1": "π/4",
                "√3": "π/3",
                "-1/√3": "-π/6",
                "-1": "-π/4",
                "-√3": "-π/3"
            }

            # 检查是否是特殊值
            value_str = Function.Trig._get_value_string(x)
            if value_str in special_values:
                return Function.Trig._parse_special_value(special_values[value_str])

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "atan", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def degrees_to_radians(x: list[Token]) -> list[Token]:
            r"""
            度数转弧度
            :param x: 度数Token流
            :return: 弧度值
            """
            # 检查是否是整数或分数
            if Calculation.is_numeric(x):
                # 特殊角度值
                degrees_dict = {
                    30: "π/6",
                    45: "π/4",
                    60: "π/3",
                    90: "π/2",
                    120: "2π/3",
                    135: "3π/4",
                    150: "5π/6",
                    180: "π",
                    210: "7π/6",
                    225: "5π/4",
                    240: "4π/3",
                    270: "3π/2",
                    300: "5π/3",
                    315: "7π/4",
                    330: "11π/6",
                    360: "2π"
                }

                # 对于整数度数，检查是否是特殊角度
                if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                    degree = int(x[0].value) % 360
                    if degree in degrees_dict:
                        return Function.Trig._parse_special_value(degrees_dict[degree])

                # 对于分数度数，转换为弧度的分数形式
                num, den = Calculation.to_fraction(x)

                # 弧度 = 度数 × (π/180)
                pi_num, pi_den = 1, 180

                # 计算 num/den × pi/180 = (num × pi)/(den × 180)
                result_num = num
                result_den = den * 180

                # 约分
                g = gcd(abs(result_num), abs(result_den))
                result_num //= g
                result_den //= g

                # 根据分子分母创建结果
                if result_num == 0:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

                if result_den == 1:
                    if result_num == 1:
                        return [Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0])]
                    else:
                        return [
                            Token(Token.TYPE.INTEGER, str(result_num), [0, 0]),
                            Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                            Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0])
                        ]

                # 形如 num*π/den
                return [
                    Token(Token.TYPE.INTEGER, str(result_num), [0, 0]),
                    Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0]),
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    Token(Token.TYPE.INTEGER, str(result_den), [0, 0])
                ] if result_num == 1 else [
                    Token(Token.TYPE.INTEGER, str(result_num), [0, 0]),
                    Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                    Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0]),
                    Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                    Token(Token.TYPE.INTEGER, str(result_den), [0, 0])
                ]

            # 无法直接计算的情况，保持原样并添加π/180的系数
            return [
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0]),
                Token(Token.TYPE.OPERATOR, "*", [0, 0]),
                Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0]),
                Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                Token(Token.TYPE.INTEGER, "180", [0, 0])
            ]

        @staticmethod
        def _get_angle_string(x: list[Token]) -> str:
            r"""
            将角度Token流转换为标准化的字符串表示
            :param x: 角度Token流
            :return: 标准化的角度字符串
            """
            # 简单情况：单个Token如π、π/2等
            if len(x) == 1:
                return x[0].value
            elif len(x) == 3 and x[1].value == "/":
                # 形如π/6等分数形式
                return f"{x[0].value}/{x[2].value}"
            elif len(x) == 3 and x[1].value == "*" and x[0].type == Token.TYPE.INTEGER and x[2].value == "π":
                # 形如2*π
                return f"{x[0].value}π"
            elif len(x) >= 3 and x[0].type == Token.TYPE.INTEGER and x[1].value == "π" and x[2].value == "/":
                # 形如2π/3
                return f"{x[0].value}π/{x[-1].value}"

            # 默认情况
            return ''.join([t.value for t in x])

        @staticmethod
        def _get_value_string(x: list[Token]) -> str:
            r"""
            将值Token流转换为标准化的字符串表示，用于查找特殊值
            :param x: 值Token流
            :return: 标准化的值字符串
            """
            if len(x) == 1:
                return x[0].value
            elif len(x) == 3 and x[1].value == "/":
                # 分数形式 a/b
                return f"{x[0].value}/{x[2].value}"
            elif len(x) >= 3 and x[0].value == "√" and x[2].value == "/":
                # 形如 √a/b
                return f"√{x[1].value}/{x[3].value}"

            # 默认情况
            return ''.join([t.value for t in x])

        @staticmethod
        def _parse_special_value(value_str: str) -> list[Token]:
            r"""
            解析特殊值字符串为Token列表
            :param value_str: 特殊值字符串
            :return: Token列表
            """
            # 简单值：0、1等
            if value_str in ["0", "1", "-1"]:
                return [Token(Token.TYPE.INTEGER, value_str, [0, 0])]

            # 分数形式：1/2、√3/2等
            if "/" in value_str:
                parts = value_str.split("/")

                if parts[0] == "1" and parts[1] == "√2":
                    # 1/√2 形式
                    return [
                        Token(Token.TYPE.INTEGER, "1", [0, 0]),
                        Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                        Token(Token.TYPE.OPERATOR, "√", [0, 0]),
                        Token(Token.TYPE.INTEGER, "2", [0, 0])
                    ]

                if parts[0] == "√3":
                    # √3 形式或 √3/2 形式
                    sqrt_tokens = [
                        Token(Token.TYPE.OPERATOR, "√", [0, 0]),
                        Token(Token.TYPE.INTEGER, "3", [0, 0])
                    ]

                    if parts[1] == "1":
                        return sqrt_tokens
                    else:
                        return sqrt_tokens + [
                            Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                            Token(Token.TYPE.INTEGER, parts[1], [0, 0])
                        ]

                if parts[0] == "1" and parts[1] == "√3":
                    # 1/√3 形式
                    return [
                        Token(Token.TYPE.INTEGER, "1", [0, 0]),
                        Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                        Token(Token.TYPE.OPERATOR, "√", [0, 0]),
                        Token(Token.TYPE.INTEGER, "3", [0, 0])
                    ]

                # 普通分数
                if "√" not in value_str and "π" not in value_str:
                    return [
                        Token(Token.TYPE.INTEGER, parts[0], [0, 0]),
                        Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                        Token(Token.TYPE.INTEGER, parts[1], [0, 0])
                    ]

                # π相关分数
                if "π" in parts[0]:
                    pi_parts = parts[0].split("π")

                    if pi_parts[0] == "":
                        # π/n 形式
                        return [
                            Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0]),
                            Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                            Token(Token.TYPE.INTEGER, parts[1], [0, 0])
                        ]
                    else:
                        # mπ/n 形式
                        return [
                            Token(Token.TYPE.INTEGER, pi_parts[0], [0, 0]),
                            Token(Token.TYPE.NATIVE_IRRATIONAL, "π", [0, 0]),
                            Token(Token.TYPE.OPERATOR, "/", [0, 0]),
                            Token(Token.TYPE.INTEGER, parts[1], [0, 0])
                        ]

            # 其他情况：直接解析为简单的Token序列
            return [Token(Token.TYPE.INTEGER, value_str, [0, 0])]

    class Log:
        r"""
        对数函数相关功能
        """

        @staticmethod
        def log(base: list[Token], x: list[Token]) -> list[Token]:
            r"""
            计算对数函数
            :param base: 底数Token流
            :param x: 真数Token流
            :return: 计算结果
            """
            # 检查参数有效性
            if Calculation.is_zero(x) or Calculation.is_zero(base) or Calculation.is_one(base):
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DOMAIN_ERROR,
                    "Logarithm domain error",
                    [0],
                    primary_info="log domain error: x>0, base>0, base≠1"
                )

            # 特殊情况: log_base(1) = 0
            if Calculation.is_one(x):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 特殊情况: log_base(base) = 1
            if Function.Log._tokens_equal_ignore_format(base, x):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 特殊情况: log_base(x^n) = n * log_base(x)
            if Calculation._is_variable_power(x):
                power_base = Calculation._get_power_base(x)
                power_exp = Calculation._get_power_exponent(x)

                # 如果底数等于幂的底数
                if Function.Log._tokens_equal_ignore_format([base[0]], [power_base]):
                    return power_exp

                # 一般情况：log_base(y^n) = n * log_base(y)
                log_of_base = [
                    Token(Token.TYPE.FUNCTION, "log", [0, 0]),
                    Token(Token.TYPE.LBRACKET, "(", [0, 0]),
                    base[0],
                    Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0]),
                    power_base,
                    Token(Token.TYPE.RBRACKET, ")", [0, 0])
                ]

                if Calculation.is_one(power_exp):
                    return log_of_base
                else:
                    return power_exp + [
                        Token(Token.TYPE.OPERATOR, "*", [0, 0])
                    ] + log_of_base

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "log", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0]),
                base[0],
                Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def ln(x: list[Token]) -> list[Token]:
            r"""
            计算自然对数函数
            :param x: 真数Token流
            :return: 计算结果
            """
            # 使用e为底数的对数
            e_token = [Token(Token.TYPE.NATIVE_IRRATIONAL, "𝑒", [0, 0])]
            return Function.Log.log(e_token, x)

        @staticmethod
        def lg(x: list[Token]) -> list[Token]:
            r"""
            计算常用对数函数（以10为底）
            :param x: 真数Token流
            :return: 计算结果
            """
            # 使用10为底数的对数
            base_10 = [Token(Token.TYPE.INTEGER, "10", [0, 0])]
            return Function.Log.log(base_10, x)

        @staticmethod
        def exp(x: list[Token]) -> list[Token]:
            r"""
            计算自然指数函数 e^x
            :param x: 指数Token流
            :return: 计算结果
            """
            # 使用e^x表示
            e_token = [Token(Token.TYPE.NATIVE_IRRATIONAL, "𝑒", [0, 0])]
            return Function.Pow.pow(e_token, x)

        @staticmethod
        def _tokens_equal_ignore_format(tokens1: list[Token], tokens2: list[Token]) -> bool:
            r"""
            比较两个Token列表是否在数学上等价（忽略格式差异）
            :param tokens1: 第一个Token列表
            :param tokens2: 第二个Token列表
            :return: 是否等价
            """
            # 简单情况：直接比较
            if len(tokens1) == 1 and len(tokens2) == 1:
                return tokens1[0].value == tokens2[0].value

            # 复杂情况：需要更复杂的比较逻辑
            # 这里简化处理，实际应该进行更深入的数学等价判断
            return False

    class Other:
        r"""
        其他数学函数
        """

        @staticmethod
        def abs(x: list[Token]) -> list[Token]:
            r"""
            计算绝对值函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 处理整数和分数
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)
                abs_value = abs(value)
                return [Token(Token.TYPE.INTEGER, str(abs_value), [0, 0])]

            if len(x) == 3 and x[1].value == "/":
                num = int(x[0].value)
                den = int(x[2].value)
                abs_num = abs(num)
                abs_den = abs(den)
                return Calculation.create_fraction(abs_num, abs_den)

            # 处理变量和无理数
            if len(x) == 1 and x[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM,
                                             Token.TYPE.NATIVE_IRRATIONAL]:
                # 检查是否是带有负数标记的变量
                if "-?" in x[0].value:
                    # 去除负号标记，返回正变量
                    var_name = x[0].value.replace("-?", "?") if "?" in x[0].value else x[0].value.replace("-", "")
                    return [Token(x[0].type, var_name, x[0].range)]
                return x  # 默认为正

            # 处理负数表达式
            if len(x) >= 2 and x[0].value == "-":
                # 去除负号，返回余下表达式
                return x[1:] if len(x) == 2 else x[2:-1]  # 处理有括号的情况

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "abs", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def fact(x: list[Token]) -> list[Token]:
            r"""
            计算阶乘函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 检查是否是非负整数
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)

                if value < 0:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DOMAIN_ERROR,
                        "Factorial domain error",
                        [0],
                        primary_info=f"factorial is undefined for negative numbers: {value}!"
                    )

                # 计算阶乘
                try:
                    result = 1
                    for i in range(1, value + 1):
                        result *= i

                    return [Token(Token.TYPE.INTEGER, str(result), [0, 0])]
                except OverflowError:
                    # 结果太大，保持原始表达式形式
                    pass

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "fact", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def gcd(a: list[Token], b: list[Token]) -> list[Token]:
            r"""
            计算最大公约数
            :param a: 第一个参数Token流
            :param b: 第二个参数Token流
            :return: 计算结果
            """
            # 检查参数是否为整数
            if len(a) == 1 and a[0].type == Token.TYPE.INTEGER and len(b) == 1 and b[0].type == Token.TYPE.INTEGER:
                num_a = int(a[0].value)
                num_b = int(b[0].value)

                # 计算GCD
                result = gcd(abs(num_a), abs(num_b))
                return [Token(Token.TYPE.INTEGER, str(result), [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "gcd", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + a + [
                Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0])
            ] + b + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def lcm(a: list[Token], b: list[Token]) -> list[Token]:
            r"""
            计算最小公倍数
            :param a: 第一个参数Token流
            :param b: 第二个参数Token流
            :return: 计算结果
            """
            # 检查参数是否为整数
            if len(a) == 1 and a[0].type == Token.TYPE.INTEGER and len(b) == 1 and b[0].type == Token.TYPE.INTEGER:
                num_a = int(a[0].value)
                num_b = int(b[0].value)

                # 如果任一数为0，LCM为0
                if num_a == 0 or num_b == 0:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

                # 计算LCM
                result = lcm(abs(num_a), abs(num_b))
                return [Token(Token.TYPE.INTEGER, str(result), [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "lcm", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + a + [
                Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0])
            ] + b + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def mod(a: list[Token], b: list[Token]) -> list[Token]:
            r"""
            计算模运算（取余）
            :param a: 被除数Token流
            :param b: 除数Token流
            :return: 计算结果
            """
            # 检查除数是否为0
            if Calculation.is_zero(b):
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                    "Modulo by zero",
                    [0],
                    primary_info="cannot calculate modulo with zero divisor"
                )

            # 检查参数是否为整数
            if len(a) == 1 and a[0].type == Token.TYPE.INTEGER and len(b) == 1 and b[0].type == Token.TYPE.INTEGER:
                num_a = int(a[0].value)
                num_b = int(b[0].value)

                # 计算模运算
                result = num_a % num_b
                return [Token(Token.TYPE.INTEGER, str(result), [0, 0])]

            # 无法直接计算的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "mod", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + a + [
                Token(Token.TYPE.PARAM_SEPARATOR, ",", [0, 0])
            ] + b + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]

        @staticmethod
        def sign(x: list[Token]) -> list[Token]:
            r"""
            计算符号函数
            :param x: 参数Token流
            :return: 计算结果
            """
            # 处理整数和分数
            if len(x) == 1 and x[0].type == Token.TYPE.INTEGER:
                value = int(x[0].value)
                if value > 0:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]
                elif value < 0:
                    return [Token(Token.TYPE.INTEGER, "-1", [0, 0])]
                else:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            if len(x) == 3 and x[1].value == "/":
                num = int(x[0].value)
                if num > 0:
                    return [Token(Token.TYPE.INTEGER, "1", [0, 0])]
                elif num < 0:
                    return [Token(Token.TYPE.INTEGER, "-1", [0, 0])]
                else:
                    return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 处理负数表达式
            if len(x) >= 2 and x[0].value == "-":
                return [Token(Token.TYPE.INTEGER, "-1", [0, 0])]

            # 无法确定符号的情况，保持函数形式
            return [
                Token(Token.TYPE.FUNCTION, "sign", [0, 0]),
                Token(Token.TYPE.LBRACKET, "(", [0, 0])
            ] + x + [
                Token(Token.TYPE.RBRACKET, ")", [0, 0])
            ]


"""test"""
if __name__ == "__main__":
    from oloc_lexer import Lexer
    from oloc_parser import Parser
    from oloc_preprocessor import Preprocessor


    def test_expression(expr, expected=None):
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
            result = evaluator.expression
            print(f"Result: {result}")
            if expected is not None:
                print(f"Expected result: {expected}")
                print(f"Match: {'✓' if result == expected else '✗'}")

            print("Calculation steps:")
            for i, step in enumerate(evaluator.result):
                step_expr = ' '.join([token.value for token in step])
                print(f"  Step {i}: {step_expr}")

        except Exception as e:
            print(f"Error: {e}")


    # 测试用例1: 基本整数加法
    test_expression("1+2", "3")

    # 测试用例2: 基本整数四则运算
    test_expression("2*3+4", "10")

    # 测试用例3: 带括号的表达式
    test_expression("(2+3)*4", "20")

    # 测试用例4: 分数运算
    test_expression("1/2+3/4", "5/4")

    # 测试用例5: 带负数的运算
    test_expression("-5+7", "2")

    # 测试用例6: 幂运算
    test_expression("2^3", "8")

    # 测试用例7: 函数调用
    test_expression("sqrt(16)", "4")

    # 测试用例8: 包含无理数的表达式
    test_expression("2*π", "2π")

    # 测试用例9: 复杂表达式
    test_expression("(3+4)*(5-2)/sqrt(16)", "21/4")

    # 测试用例10: 多层嵌套表达式
    test_expression("((2+3)^2-1)/((4*5)+(6/3))", "12/11")

    # 测试用例11: 基本分数运算
    test_expression("3/4*2/3", "1/2")

    # 测试用例12: 负数幂运算
    test_expression("2^(-3)", "1/8")

    # 测试用例13: 带有无理数的复杂运算
    test_expression("π^2+e^2", "π^2+𝑒^2")

    # 测试用例14: 函数嵌套
    test_expression("sqrt(sqrt(16))", "2")

    # 测试用例15: 复杂分数运算
    test_expression("(1/2+1/3)/(1/4+1/5)", "50/27")

    # 测试用例16: 变量相乘
    test_expression("π*π", "π^2")

    # 测试用例17: 变量相除
    test_expression("x/x", "1")

    # 测试用例18: 零值测试
    test_expression("0+5", "5")

    # 测试用例19: 单位值测试
    test_expression("1*7", "7")

    # 测试用例20: 除零错误测试
    test_expression("5/0", "Error")

    # 测试用例21: 同类项合并
    test_expression("2*x+3*x", "5x")

    # 测试用例22: 三角函数
    test_expression("sin(π/6)", "1/2")

    # 测试用例23: 对数函数
    test_expression("log(10,100)", "2")

    # 测试用例24: 复合函数
    test_expression("ln(e^2)", "2")

    # 测试用例25: 多变量运算
    test_expression("3*x/5*y", "3xy/5")

    # 测试用例26: 绝对值函数
    test_expression("|(-3)|", "3")

    # 测试用例27: 阶乘函数
    test_expression("fact(5)", "120")

    # 测试用例28: GCD和LCM
    test_expression("gcd(12,18)", "6")
    test_expression("lcm(4,6)", "12")

    # 测试用例29: 角度转弧度
    test_expression("45°", "π/4")

    # 测试用例30: 复杂变量幂
    test_expression("x^2*x^3", "x^5")
    
r"""
:author: WaterRun
:date: 2025-04-07
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

import time

from oloc_token import Token
from oloc_lexer import Lexer
from oloc_ast import ASTTree, ASTNode
from oloc_exceptions import *


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
        self.result: list[list[Token]] = [self.tokens]
        self.time_cost = -1

    def __repr__(self):
        result = (f"Evaluator: \n"
                  f"expression: {self.expression}\n"
                  f"expression (spilt between token): ")
        for token in self.tokens:
            result += f"{token.value} "
        result += "\ntoken flow: \n"
        for index, token in enumerate(self.tokens):
            result += f"{index}\t{token}\n"
        result += f"ast: \n{self.ast}"
        result += "\n result:\n"
        for result_index, result_list in enumerate(self.result):
            result += f"{result_index}: {result_list}"
        result += f"\ntime cost: {'(Not execute)' if self.time_cost == -1 else self.time_cost / 1000000} ms\n"
        return result

    def _evaluate(self):
        r"""
        执行求值
        :return: None
        """
        # 初始化结果历史记录
        self.result = [self.tokens.copy()]

        # 递归求值AST树
        final_tokens = self._evaluate_node(self.ast.root)

        # 更新最终结果
        self.tokens = final_tokens

        # 更新表达式字符串
        updated_tokens, updated_expr = Lexer.update(final_tokens)
        self.tokens = updated_tokens
        self.expression = updated_expr

        # 确保最终结果添加到历史中
        if self.result[-1] != final_tokens:
            self.result.append(final_tokens)

    def _evaluate_node(self, node):
        """
        递归评估AST节点
        :param node: 要评估的节点
        :return: 计算结果的Token列表
        """
        # 字面量节点
        if node.type == ASTNode.TYPE.LITERAL:
            # 假设字面量节点的第一个token是其值
            return [node.tokens[0]]

        # 分组表达式节点
        elif node.type == ASTNode.TYPE.GRP_EXP:
            # 假设分组表达式有一个子节点表示其内容
            if len(node.children) != 1:
                raise Exception(f"GroupExpression should have exactly one child, got {len(node.children)}")

            # 递归计算分组内的表达式
            inner_result = self._evaluate_node(node.children[0])

            # 记录中间状态
            self._record_intermediate_state(inner_result)

            # 对于简单结果（单个Token），直接返回
            if len(inner_result) == 1:
                return inner_result

            # 对于复杂结果，保留括号
            l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
            r_bracket = Token(Token.TYPE.RBRACKET, ")", [0,0])
            result = [l_bracket] + inner_result + [r_bracket]
            return result

        # 二元表达式节点
        elif node.type == ASTNode.TYPE.BIN_EXP:
            # 假设二元表达式有两个子节点和一个operator token
            if len(node.children) != 2:
                raise Exception(f"BinaryExpression should have exactly two children, got {len(node.children)}")

            # 计算左子树
            left_result = self._evaluate_node(node.children[0])

            # 记录左子树计算后的状态
            self._record_intermediate_state(left_result)

            # 计算右子树
            right_result = self._evaluate_node(node.children[1])

            # 记录右子树计算后的状态
            self._record_intermediate_state(right_result)

            # 根据操作符执行相应的计算
            # 假设操作符是节点的第一个token
            operator = node.tokens[0].value

            if operator == "+":
                result = self.addition(left_result, right_result)
            elif operator == "-":
                result = self.subtraction(left_result, right_result)
            elif operator == "*":
                result = self.multiplication(left_result, right_result)
            elif operator == "/":
                result = self.division(left_result, right_result)
            elif operator == "^":
                # 幂运算
                result = Function.Pow.pow(left_result, right_result)
            else:
                # 不支持的运算符
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                    self.expression,
                    [node.tokens[0].range[0]],
                    primary_info=f"Unsupported operator: {operator}"
                )

            # 记录计算结果
            self._record_intermediate_state(result)

            return result

        # 一元表达式节点
        elif node.type == ASTNode.TYPE.URY_EXP:
            # 假设一元表达式有一个子节点和一个operator token
            if len(node.children) != 1:
                raise Exception(f"UnaryExpression should have exactly one child, got {len(node.children)}")

            # 计算子表达式
            operand_result = self._evaluate_node(node.children[0])

            # 记录子表达式计算后的状态
            self._record_intermediate_state(operand_result)

            # 根据一元运算符执行计算
            # 假设操作符是节点的第一个token
            operator = node.tokens[0].value

            if operator == "-":
                result = self._negate_expression(operand_result)
            elif operator == "+":
                result = operand_result  # 正号不改变值
            elif operator == "√":
                # 平方根运算
                result = Function.Pow.sqrt(operand_result)
            else:
                # 不支持的一元运算符
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                    self.expression,
                    [node.tokens[0].range[0]],
                    primary_info=f"Unsupported unary operator: {operator}"
                )

            # 记录计算结果
            self._record_intermediate_state(result)

            return result

        # 函数调用节点
        elif node.type == ASTNode.TYPE.FUN_CAL:
            # 假设函数调用有多个子节点（参数）和一个function token

            # 计算所有参数
            args_results = []
            for child in node.children:
                arg_result = self._evaluate_node(child)
                args_results.append(arg_result)
                # 记录参数计算后的状态
                self._record_intermediate_state(arg_result)

            # 假设函数名是节点的第一个token
            func_name = node.tokens[0].value

            if func_name == "pow":
                if len(args_results) != 2:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                        self.expression,
                        [node.tokens[0].range[0]],
                        primary_info="pow",
                        secondary_info="expected 2 arguments"
                    )
                result = Function.Pow.pow(args_results[0], args_results[1])
            elif func_name == "sqrt":
                if len(args_results) != 1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                        self.expression,
                        [node.tokens[0].range[0]],
                        primary_info="sqrt",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sqrt(args_results[0])
            elif func_name == "sq":
                if len(args_results) != 1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                        self.expression,
                        [node.tokens[0].range[0]],
                        primary_info="sq",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sq(args_results[0])
            elif func_name == "cub":
                if len(args_results) != 1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                        self.expression,
                        [node.tokens[0].range[0]],
                        primary_info="cub",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.cub(args_results[0])
            elif func_name == "rec":
                if len(args_results) != 1:
                    raise OlocCalculationError(
                        OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                        self.expression,
                        [node.tokens[0].range[0]],
                        primary_info="rec",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.rec(args_results[0])
            else:
                # 不支持的函数
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.DIVIDE_BY_ZERO,  # 临时使用此类型
                    self.expression,
                    [node.tokens[0].range[0]],
                    primary_info=f"Unsupported function: {func_name}"
                )

            # 记录函数计算后的状态
            self._record_intermediate_state(result)

            return result

        # 未知节点类型
        else:
            raise Exception(f"Unknown node type: {node.type}")

    def _record_intermediate_state(self, tokens):
        """
        记录中间计算状态到结果历史中
        :param tokens: 当前计算的Token列表
        """
        # 避免添加重复的状态
        if self.result and tokens != self.result[-1]:
            # 创建深拷贝以避免后续修改影响历史记录
            self.result.append(tokens.copy())

    def _negate(self, tokens):
        """
        对Token列表执行取反操作
        :param tokens: 要取反的Token列表
        :return: 取反后的结果
        """
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            # 整数取反
            value = str(-int(tokens[0].value))
            return [Token(Token.TYPE.INTEGER, value, [0, len(value) - 1])]
        elif len(tokens) == 3 and tokens[1].value == "/":
            # 分数取反，取反分子
            num = -int(tokens[0].value)
            den = int(tokens[2].value)
            num_str = str(num)
            num_token = Token(Token.TYPE.INTEGER, num_str, [0, len(num_str) - 1])
            return [num_token, tokens[1], tokens[2]]
        else:
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

    def execute(self):
        r"""
        执行求值器
        :return: None
        """
        start_time = time.time_ns()
        self._evaluate()
        self.time_cost = time.time_ns() - start_time

    r"""
    静态方法
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
        if Evaluator._is_zero(augend):
            return addend
        if Evaluator._is_zero(addend):
            return augend

        # 2. 处理整数和分数的加法
        if Evaluator._is_numeric(augend) and Evaluator._is_numeric(addend):
            return Evaluator._add_numeric(augend, addend)

        # 3. 处理变量情况

        # 3.1 同类型变量
        if (len(augend) == 1 and len(addend) == 1 and
                augend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM] and
                addend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM] and
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
        if Evaluator._is_zero(subtrahend):
            return minuend

        # 2. 特殊情况: 被减数为0
        if Evaluator._is_zero(minuend):
            return Evaluator._negate_expression(subtrahend)

        # 3. 处理整数和分数的减法
        if Evaluator._is_numeric(minuend) and Evaluator._is_numeric(subtrahend):
            # 转换为加法: a - b = a + (-b)
            negated_subtrahend = Evaluator._negate_expression(subtrahend)
            return Evaluator._add_numeric(minuend, negated_subtrahend)

        # 4. 处理变量情况

        # 4.1 同类型变量
        if (len(minuend) == 1 and len(subtrahend) == 1 and
                minuend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM] and
                subtrahend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM] and
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
        if Evaluator._is_zero(factor_1) or Evaluator._is_zero(factor_2):
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 2. 特殊情况: 任一因数为1
        if Evaluator._is_one(factor_1):
            return factor_2
        if Evaluator._is_one(factor_2):
            return factor_1

        # 3. 处理整数和分数的乘法
        if Evaluator._is_numeric(factor_1) and Evaluator._is_numeric(factor_2):
            return Evaluator._multiply_numeric(factor_1, factor_2)

        # 4. 处理变量与数值的乘法

        # 4.1 数值 * 变量
        if (Evaluator._is_numeric(factor_1) and len(factor_2) == 1 and
                factor_2[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL]):
            # 整数/分数 * 变量
            return factor_1 + [Token(Token.TYPE.OPERATOR, "*", [0, 0])] + factor_2

        # 4.2 变量 * 数值
        if (Evaluator._is_numeric(factor_2) and len(factor_1) == 1 and
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
        if Evaluator._is_zero(divisor):
            raise OlocCalculationError(
                OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                "Division by zero",
                [0],  # 位置信息需要更准确
                primary_info="division by zero"
            )

        # 2. 特殊情况: 被除数为0
        if Evaluator._is_zero(dividend):
            return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

        # 3. 特殊情况: 除数为1
        if Evaluator._is_one(divisor):
            return dividend

        # 4. 处理整数和分数的除法
        if Evaluator._is_numeric(dividend) and Evaluator._is_numeric(divisor):
            # 转换为乘法: a / b = a * (1/b)
            reciprocal = Evaluator._get_reciprocal(divisor)
            return Evaluator._multiply_numeric(dividend, reciprocal)

        # 5. 处理变量与整数/分数的除法
        if (len(dividend) == 1 and
                dividend[0].type in [Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM, Token.TYPE.NATIVE_IRRATIONAL] and
                Evaluator._is_numeric(divisor)):
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

        # 6. 无法化简的情况，保持原始表达式形式
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
    def _is_zero(tokens: list[Token]) -> bool:
        """判断Token列表是否表示0"""
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "0":
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "0"):
            return True

        return False

    @staticmethod
    def _is_one(tokens: list[Token]) -> bool:
        """判断Token列表是否表示1"""
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == "1":
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[0].value == tokens[2].value):
            return True

        return False

    @staticmethod
    def _is_numeric(tokens: list[Token]) -> bool:
        """判断Token列表是否表示纯数值（整数或分数）"""
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            return True

        if (len(tokens) == 3 and tokens[1].value == "/" and
            tokens[0].type == Token.TYPE.INTEGER and tokens[2].type == Token.TYPE.INTEGER):
            return True

        return False

    @staticmethod
    def _to_fraction(tokens: list[Token]) -> tuple:
        """将Token列表转换为分数表示（分子,分母）"""
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            return int(tokens[0].value), 1

        if len(tokens) == 3 and tokens[1].value == "/":
            return int(tokens[0].value), int(tokens[2].value)

        raise ValueError(f"Cannot convert to fraction: {tokens}")

    @staticmethod
    def _add_numeric(a: list[Token], b: list[Token]) -> list[Token]:
        """处理纯数值（整数或分数）的加法"""
        # 转换为分数形式
        num_a, den_a = Evaluator._to_fraction(a)
        num_b, den_b = Evaluator._to_fraction(b)

        # 计算: a/b + c/d = (a*d + c*b)/(b*d)
        num_result = num_a * den_b + num_b * den_a
        den_result = den_a * den_b

        # 化简
        return Evaluator._create_fraction(num_result, den_result)

    @staticmethod
    def _multiply_numeric(a: list[Token], b: list[Token]) -> list[Token]:
        """处理纯数值（整数或分数）的乘法"""
        # 转换为分数形式
        num_a, den_a = Evaluator._to_fraction(a)
        num_b, den_b = Evaluator._to_fraction(b)

        # 计算: (a/b) * (c/d) = (a*c)/(b*d)
        num_result = num_a * num_b
        den_result = den_a * den_b

        # 化简
        return Evaluator._create_fraction(num_result, den_result)

    @staticmethod
    def _negate_expression(tokens: list[Token]) -> list[Token]:
        """对表达式取反"""
        if len(tokens) == 1 and tokens[0].type == Token.TYPE.INTEGER:
            # 整数取反
            value = str(-int(tokens[0].value))
            return [Token(Token.TYPE.INTEGER, value, [0, len(value) - 1])]

        if len(tokens) == 3 and tokens[1].value == "/":
            # 分数取反，取反分子
            num = -int(tokens[0].value)
            den = int(tokens[2].value)
            return Evaluator._create_fraction(num, den)

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
    def _get_reciprocal(tokens: list[Token]) -> list[Token]:
        """计算倒数"""
        num, den = Evaluator._to_fraction(tokens)

        # 检查分子是否为0
        if num == 0:
            raise OlocCalculationError(
                OlocCalculationError.TYPE.DIVIDE_BY_ZERO,
                "Division by zero",
                [0],
                primary_info="reciprocal of zero"
            )

        # 计算倒数: (a/b)^-1 = b/a
        return Evaluator._create_fraction(den, num)

    @staticmethod
    def _create_fraction(numerator: int, denominator: int) -> list[Token]:
        """创建分数Token列表，自动化简"""
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
            result_value = str(numerator)  # 确保是字符串
            # 创建Token时确保token_value参数位置正确
            return [Token(Token.TYPE.INTEGER, result_value, [0, len(result_value) - 1])]
        else:
            # 分数结果
            num_str = str(numerator)  # 确保是字符串
            den_str = str(denominator)  # 确保是字符串

            # 确保参数顺序正确: (token_type, token_value, token_range)
            num_token = Token(Token.TYPE.INTEGER, num_str, [0, len(num_str) - 1])
            op_token = Token(Token.TYPE.OPERATOR, "/", [len(num_str), len(num_str)])
            den_token = Token(Token.TYPE.INTEGER, den_str,
                              [len(num_str) + 1, len(num_str) + len(den_str)])
            return [num_token, op_token, den_token]


class Function:
    r"""
    函数
    """

    """
    代数函数
    """

    class Pow:
        r"""
        指数函数
        """

        @staticmethod
        def pow(x: list[Token], y: list[Token]) -> list[Token]:
            r"""
            计算指数函数
            :param x: 底数Token流
            :param y: 次数Token流
            :return: 计算结果
            """
            # 特殊情况: 0^0
            if Evaluator._is_zero(x) and Evaluator._is_zero(y):
                raise OlocCalculationError(
                    OlocCalculationError.TYPE.ZERO_TO_THE_POWER_OF_ZERO,
                    "Zero to the power of zero",
                    [0],
                    primary_info="0^0"
                )

            # 特殊情况: x^0 = 1
            if Evaluator._is_zero(y):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

            # 特殊情况: x^1 = x
            if Evaluator._is_one(y):
                return x

            # 特殊情况: 0^y = 0 (y不为0)
            if Evaluator._is_zero(x):
                return [Token(Token.TYPE.INTEGER, "0", [0, 0])]

            # 特殊情况: 1^y = 1
            if Evaluator._is_one(x):
                return [Token(Token.TYPE.INTEGER, "1", [0, 0])]

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
                num, den = Evaluator._to_fraction(x)
                exponent = int(y[0].value)

                if exponent > 0:
                    # 正整数次幂: (a/b)^n = a^n/b^n
                    num_result = num ** exponent
                    den_result = den ** exponent
                    return Evaluator._create_fraction(num_result, den_result)
                elif exponent < 0:
                    # 负整数次幂: (a/b)^(-n) = (b/a)^n
                    exponent = -exponent
                    num_result = den ** exponent
                    den_result = num ** exponent
                    return Evaluator._create_fraction(num_result, den_result)

            # 无法直接计算的情况，保持原始表达式形式
            return x + [Token(Token.TYPE.OPERATOR, "^", [0, 0])] + y

        @staticmethod
        def sqrt(x: list[Token]) -> list[Token]:
            r"""
            计算开根号函数
            :param x: 被开根号的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("1/2"))

        @staticmethod
        def sq(x: list[Token]) -> list[Token]:
            r"""
            计算二次方函数
            :param x: 被二次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("2"))

        @staticmethod
        def cub(x: list[Token]) -> list[Token]:
            r"""
            计算三次方函数
            :param x: 被三次方的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("3"))

        @staticmethod
        def rec(x: list[Token]) -> list[Token]:
            r"""
            计算倒数函数
            :param x: 被计算倒数的数
            :return: 计算结果
            """
            return Function.Pow.pow(x, Lexer.tokenizer("-1"))

    """
    超越函数
    """

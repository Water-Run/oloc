r"""
:author: WaterRun
:date: 2025-04-21
:file: oloc_evaluator.py
:description: Oloc evaluator
"""

import time

from oloc_token import Token
from oloc_ast import ASTTree, ASTNode
from oloc_lexer import Lexer
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
                  f"expression (split between token): ")
        for token in self.tokens:
            result += f"{token.value} "
        result += "\ntoken flow: \n"
        for index, token in enumerate(self.tokens):
            result += f"{index}\t{token}\n"
        result += f"ast: \n{self.ast}"
        result += "\n result:\n"
        for result_index, result_list in enumerate(self.result):
            result += f"{result_index}: {result_list}\n"
        result += f"\ntime cost: {'(Not execute)' if self.time_cost == -1 else self.time_cost / 1000000} ms\n"
        return result

    def _evaluate(self):
        r"""
        执行求值
        :return: None
        """
        # 初始化结果历史记录，开始只有原始表达式
        self.result = [self.tokens.copy()]

        # 递归求值AST树
        final_tokens = self._evaluate_node(self.ast.root)

        # 更新表达式字符串
        self.tokens, self.expression = Lexer.update(final_tokens)

        # 确保最终结果添加到历史中
        if self.result[-1] != final_tokens:
            self.result.append(final_tokens)

    def _evaluate_node(self, node):
        """
        递归评估AST节点
        :param node: 要评估的节点
        :return: 计算结果的Token列表
        """
        # 字面量节点直接返回其值
        if node.type == ASTNode.TYPE.LITERAL:
            return [node.tokens[0]]

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

            # 记录这一步计算
            self._record_step(inner_result)

            # 如果结果简单，不需要括号
            if len(inner_result) == 1:
                return inner_result

            # 否则保留括号
            l_bracket = Token(Token.TYPE.LBRACKET, "(", [0, 0])
            r_bracket = Token(Token.TYPE.RBRACKET, ")", [0, 0])
            return [l_bracket] + inner_result + [r_bracket]

        # 二元表达式节点
        elif node.type == ASTNode.TYPE.BIN_EXP:
            if len(node.children) != 2:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [node.tokens[0].range[0] if node.tokens else 0],
                    primary_info=f"Binary expression should have exactly two children, got {len(node.children)}"
                )

            # 计算左右子表达式
            left_result = self._evaluate_node(node.children[0])
            right_result = self._evaluate_node(node.children[1])

            # 根据操作符执行计算
            operator = node.tokens[0].value

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
                    [node.tokens[0].range[0]],
                    primary_info=f"Unsupported operator: {operator}"
                )

            # 记录计算结果
            self._record_step(result)
            return result

        # 一元表达式节点
        elif node.type == ASTNode.TYPE.URY_EXP:
            if len(node.children) != 1:
                raise OlocSyntaxError(
                    OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                    self.expression,
                    [node.tokens[0].range[0] if node.tokens else 0],
                    primary_info=f"Unary expression should have exactly one child, got {len(node.children)}"
                )

            # 计算操作数
            operand_result = self._evaluate_node(node.children[0])

            # 应用一元运算符
            operator = node.tokens[0].value

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
                    [node.tokens[0].range[0]],
                    primary_info=f"Unsupported unary operator: {operator}"
                )

            # 记录计算结果
            self._record_step(result)
            return result

        # 函数调用节点
        elif node.type == ASTNode.TYPE.FUN_CAL:
            # 计算所有参数
            args_results = []
            for child in node.children:
                arg_result = self._evaluate_node(child)
                args_results.append(arg_result)

            # 执行函数计算
            func_name = node.tokens[0].value

            if func_name == "pow":
                if len(args_results) != 2:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[node.tokens[0].range[0]],
                        primary_info="pow",
                        secondary_info="expected 2 arguments"
                    )
                result = Function.Pow.pow(args_results[0], args_results[1])
            elif func_name == "sqrt":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[node.tokens[0].range[0]],
                        primary_info="sqrt",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sqrt(args_results[0])
            elif func_name == "sq":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[node.tokens[0].range[0]],
                        primary_info="sq",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.sq(args_results[0])
            elif func_name == "cub":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[node.tokens[0].range[0]],
                        primary_info="cub",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.cub(args_results[0])
            elif func_name == "rec":
                if len(args_results) != 1:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                        expression=self.expression,
                        positions=[node.tokens[0].range[0]],
                        primary_info="rec",
                        secondary_info="expected 1 argument"
                    )
                result = Function.Pow.rec(args_results[0])
            else:
                raise OlocCalculationError(
                    exception_type=OlocCalculationError.TYPE.UNSUPPORTED_FUNCTION,
                    expression=self.expression,
                    positions=[node.tokens[0].range[0]],
                    primary_info=func_name
                )

            # 记录计算结果
            self._record_step(result)
            return result

        # 未知节点类型
        else:
            raise OlocSyntaxError(
                OlocSyntaxError.TYPE.INVALID_EXPRESSION,
                self.expression,
                [0],
                primary_info=f"Unknown node type: {node.type}"
            )

    def _record_step(self, result):
        """
        记录有意义的计算步骤
        :param result: 当前计算得到的结果
        """
        # 仅当结果与上一步不同时才记录
        if self.result and self._tokens_to_str(result) != self._tokens_to_str(self.result[-1]):
            self.result.append(result.copy())

    def _tokens_to_str(self, tokens):
        """
        将Token列表转换为字符串用于比较
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
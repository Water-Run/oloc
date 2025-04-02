r"""
:author: WaterRun
:date: 2025-04-03
:file: oloc_parser.py
:description: Oloc parser
"""

import time

import oloc_utils as utils
from oloc_lexer import Lexer
from oloc_token import Token
from oloc_ast import ASTNode, ASTTree
from oloc_exceptions import *


class Parser:
    r"""
    语法分析器
    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        self.tokens, self.expression = Lexer.update(tokens)
        self.ast = None
        self.time_cost = -1
        # 用于追踪当前分析的位置
        self.current_index = 0

    def _static_check(self):
        r"""
        静态检查,确保在进入语法分析前语句的合法性
        :raise OlocSyntaxError: 当存在非法的运算符,括号或函数时,或类型错误时
        :return: None
        """

        VALID_OPERATORS = ('+', '-', '*', '/', '√', '°', '^', '%', '!', '|')
        VALID_BRACKETS = ('(', ')')
        VALID_FUNCTION = tuple(utils.get_function_mapping_table().keys())
        VALID_TYPES = (
            Token.TYPE.INTEGER,
            Token.TYPE.OPERATOR,
            Token.TYPE.RBRACKET,
            Token.TYPE.LBRACKET,
            Token.TYPE.LONG_CUSTOM,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.IRRATIONAL_PARAM,
            Token.TYPE.FUNCTION,
            Token.TYPE.PARAM_SEPARATOR,
        )

        # 使用栈跟踪绝对值符号的位置
        absolute_symbol_stack = []

        if len(self.tokens) == 0:
            self.tokens = [Token(Token.TYPE.INTEGER, "0", [0, 1])]

        for token_index, temp_token in enumerate(self.tokens):

            # 类型检查
            if temp_token.type not in VALID_TYPES:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.UNEXPECTED_TOKEN_TYPE,
                    expression=self.expression,
                    positions=list(range(*temp_token.range)),
                    primary_info=temp_token.type,
                )

            # 运算符检查
            if temp_token.type == Token.TYPE.OPERATOR:

                match temp_token.value:

                    case ".":
                        raise OlocSyntaxError(
                            exception_type=OlocSyntaxError.TYPE.DOT_SYNTAX_ERROR,
                            expression=self.expression,
                            positions=list(range(*temp_token.range)),
                            primary_info=temp_token.value,
                        )

                    case ":":
                        raise OlocSyntaxError(
                            exception_type=OlocSyntaxError.TYPE.COLON_SYNTAX_ERROR,
                            expression=self.expression,
                            positions=list(range(*temp_token.range)),
                            primary_info=temp_token.value,
                        )

                    case "|":
                        # 检查是否有不当的前缀或后缀
                        if token_index != len(self.tokens) - 1 and self.tokens[
                            token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('°', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.ENCLOSING_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if token_index > 0 and self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('*', '/', '°', '%', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.ENCLOSING_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        # 每个绝对值符号既可以是开始也可以是结束
                        # 如果栈为空，这肯定是一个开始绝对值符号
                        if not absolute_symbol_stack:
                            absolute_symbol_stack.append(token_index)
                        else:
                            # 否则，我们将其视为一个结束绝对值符号
                            # 弹出栈顶，表示匹配了一对绝对值符号
                            absolute_symbol_stack.pop()

                    case "√" | "+" | "-":

                        if not token_index != len(self.tokens) - 1:
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.PREFIX_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('*', '/', '°', '^', '%', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.PREFIX_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                    case "!" | "°":

                        if not token_index > 0:
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.POSTFIX_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.BINARY_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                    case "*" | "/" | "^" | "%":

                        if token_index not in range(1, len(self.tokens) - 1):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.BINARY_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.BINARY_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('*', '/', '°', '^', '%', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.BINARY_OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                if temp_token.value not in VALID_OPERATORS:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.UNEXPECTED_OPERATOR,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

            # 函数检查
            if temp_token.type == Token.TYPE.FUNCTION:

                if temp_token.value not in VALID_FUNCTION:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.INVALID_FUNCTION_NAME,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

                if (token_index - 1 >= 0 and self.tokens[token_index - 1].type not in (
                Token.TYPE.LBRACKET, Token.TYPE.OPERATOR, Token.TYPE.PARAM_SEPARATOR)) or \
                        (token_index + 1 == len(self.tokens) or self.tokens[
                            token_index + 1].type != Token.TYPE.LBRACKET):
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_MISPLACEMENT,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

            # 函数分隔符检查
            if temp_token.type == Token.TYPE.PARAM_SEPARATOR:
                if (token_index not in range(1, len(self.tokens) - 1)) \
                        or (self.tokens[token_index - 1].type == Token.TYPE.LBRACKET) \
                        or (self.tokens[token_index + 1].type == Token.TYPE.RBRACKET) \
                        or (self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and self.tokens[
                    token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%')) \
                        or (self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and self.tokens[
                    token_index + 1].value in ('*', '/', '^', '%')):
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_SEPARATOR_ERROR,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

            # 括号检查
            if temp_token.type in (Token.TYPE.LBRACKET, Token.TYPE.RBRACKET):

                if temp_token.value not in VALID_BRACKETS:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.UNEXPECTED_BRACKET,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

            # 无理数参数检查
            if temp_token.type == Token.TYPE.IRRATIONAL_PARAM:

                if len(self.tokens) == 0 or self.tokens[token_index - 1].type not in [
                    Token.TYPE.NATIVE_IRRATIONAL,
                    Token.TYPE.SHORT_CUSTOM,
                    Token.TYPE.LONG_CUSTOM,
                    Token.TYPE.RBRACKET,
                    Token.TYPE.INTEGER
                ]:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.IRRATIONAL_PARAM_ERROR,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

        # 检查栈中是否还有未匹配的绝对值符号
        if absolute_symbol_stack:
            # 报告第一个未匹配的绝对值符号
            mismatched_index = absolute_symbol_stack[0]
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.ABSOLUTE_SYMBOL_MISMATCH,
                expression=self.expression,
                positions=[mismatched_index],
                primary_info="|",
            )

    def _build(self):
        r"""
        构建AST
        :return: None
        """
        if not self.tokens:
            return

        self.current_index = 0
        root_node = self._parse_expression()
        self.ast = ASTTree(root_node)

    def _parse_expression(self):
        r"""
        解析整个表达式
        :return: 表达式的根节点
        """
        return self._parse_add_sub()

    def _parse_add_sub(self):
        r"""
        解析加减法表达式
        :return: 加减法表达式节点
        """
        left = self._parse_mul_div()

        while self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            if token.type == Token.TYPE.OPERATOR and token.value in ('+', '-'):
                # 创建二元表达式节点
                op_token = token
                self.current_index += 1
                right = self._parse_mul_div()

                binary_node = ASTNode(ASTNode.TYPE.BIN_EXP, [op_token])
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def _parse_mul_div(self):
        r"""
        解析乘除法和取余表达式
        :return: 乘除法表达式节点
        """
        left = self._parse_power()

        while self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            if token.type == Token.TYPE.OPERATOR and token.value in ('*', '/', '%'):
                # 创建二元表达式节点
                op_token = token
                self.current_index += 1
                right = self._parse_power()

                binary_node = ASTNode(ASTNode.TYPE.BIN_EXP, [op_token])
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def _parse_power(self):
        r"""
        解析幂运算表达式
        :return: 幂运算表达式节点
        """
        left = self._parse_unary()

        if self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            if token.type == Token.TYPE.OPERATOR and token.value == '^':
                # 创建二元表达式节点
                op_token = token
                self.current_index += 1
                # 幂运算是右结合的
                right = self._parse_power()

                binary_node = ASTNode(ASTNode.TYPE.BIN_EXP, [op_token])
                binary_node.add_child(left)
                binary_node.add_child(right)
                return binary_node

        return left

    def _parse_unary(self):
        r"""
        解析一元运算符表达式
        :return: 一元表达式节点
        """
        if self.current_index >= len(self.tokens):
            return None

        token = self.tokens[self.current_index]

        # 处理前置一元运算符
        if token.type == Token.TYPE.OPERATOR and token.value in ('+', '-', '√', '|'):
            self.current_index += 1
            if token.value == '|':
                # 绝对值运算符需要找到匹配的右侧 |
                operand = self._parse_expression()
                if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == '|':
                    self.current_index += 1  # 跳过右侧 |
                else:
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.ABSOLUTE_SYMBOL_MISMATCH,
                        expression=self.expression,
                        positions=[token.range[0]],
                        primary_info="|"
                    )
            else:
                operand = self._parse_unary()

            unary_node = ASTNode(ASTNode.TYPE.URY_EXP, [token])
            unary_node.add_child(operand)
            return unary_node

        # 处理常规表达式后跟随后置一元运算符
        expr = self._parse_primary()

        while self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            if token.type == Token.TYPE.OPERATOR and token.value in ('!', '°'):
                self.current_index += 1
                unary_node = ASTNode(ASTNode.TYPE.URY_EXP, [token])
                unary_node.add_child(expr)
                expr = unary_node
            else:
                break

        return expr

    def _parse_primary(self):
        r"""
        解析基本元素（数字、无理数、函数调用、分组表达式）
        :return: 基本元素节点
        """
        if self.current_index >= len(self.tokens):
            return None

        token = self.tokens[self.current_index]

        # 处理字面量
        if token.type in (Token.TYPE.INTEGER, Token.TYPE.NATIVE_IRRATIONAL,
                         Token.TYPE.SHORT_CUSTOM, Token.TYPE.LONG_CUSTOM):
            self.current_index += 1
            # 检查是否有无理数参数
            if (self.current_index < len(self.tokens) and
                self.tokens[self.current_index].type == Token.TYPE.IRRATIONAL_PARAM):
                # 将无理数参数与无理数一起作为字面量处理
                param_token = self.tokens[self.current_index]
                self.current_index += 1
                return ASTNode(ASTNode.TYPE.LITERAL, [token, param_token])
            return ASTNode(ASTNode.TYPE.LITERAL, [token])

        # 处理函数调用
        elif token.type == Token.TYPE.FUNCTION:
            function_token = token
            self.current_index += 1

            # 确保有左括号
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].type != Token.TYPE.LBRACKET:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.FUNCTION_MISPLACEMENT,
                    expression=self.expression,
                    positions=list(range(*function_token.range)),
                    primary_info=function_token.value
                )

            left_bracket = self.tokens[self.current_index]
            self.current_index += 1

            # 解析函数参数
            params = self._parse_function_params()

            # 确保有右括号
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].type != Token.TYPE.RBRACKET:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.RIGHT_BRACKET_MISMATCH,
                    expression=self.expression,
                    positions=[left_bracket.range[0]],
                    primary_info=left_bracket.value
                )

            right_bracket = self.tokens[self.current_index]
            self.current_index += 1

            function_node = ASTNode(ASTNode.TYPE.FUN_CAL, [function_token, left_bracket, right_bracket])
            for param in params:
                function_node.add_child(param)

            return function_node

        # 处理分组表达式
        elif token.type == Token.TYPE.LBRACKET:
            left_bracket = token
            self.current_index += 1

            # 解析括号内的表达式
            inner_expr = self._parse_expression()

            # 确保有右括号
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].type != Token.TYPE.RBRACKET:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.LEFT_BRACKET_MISMATCH,
                    expression=self.expression,
                    positions=[left_bracket.range[0]],
                    primary_info=left_bracket.value
                )

            right_bracket = self.tokens[self.current_index]
            self.current_index += 1

            group_node = ASTNode(ASTNode.TYPE.GRP_EXP, [left_bracket, right_bracket])
            group_node.add_child(inner_expr)

            return group_node

        # 处理其他情况，这里应该不会到达，因为静态检查已经验证了所有token
        raise OlocSyntaxError(
            exception_type=OlocSyntaxError.TYPE.UNEXPECTED_TOKEN_TYPE,
            expression=self.expression,
            positions=list(range(*token.range)),
            primary_info=token.type
        )

    def _parse_function_params(self):
        r"""
        解析函数参数
        :return: 参数节点列表
        """
        params = []

        # 如果直接是右括号，表示无参数
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].type == Token.TYPE.RBRACKET:
            return params

        while True:
            # 解析一个参数
            param = self._parse_expression()
            params.append(param)

            # 检查是否结束参数列表
            if self.current_index >= len(self.tokens):
                break

            if self.tokens[self.current_index].type == Token.TYPE.RBRACKET:
                break

            # 检查参数分隔符
            if self.tokens[self.current_index].type != Token.TYPE.PARAM_SEPARATOR:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_SEPARATOR_ERROR,
                    expression=self.expression,
                    positions=list(range(*self.tokens[self.current_index].range)),
                    primary_info=self.tokens[self.current_index].value
                )

            self.current_index += 1  # 跳过分隔符

        return params

    def _syntax_check(self):
        r"""
        语法检查
        :return: None
        """
        if not self.ast or not self.ast.root:
            return

        # 深度优先遍历AST进行语法检查
        self._check_node(self.ast.root)

    def _check_node(self, node):
        r"""
        检查单个节点的语法正确性
        :param node: 要检查的节点
        :raise OlocSyntaxError: 当节点语法不正确时
        :return: None
        """
        if not node:
            return

        # 根据节点类型进行检查
        if node.type == ASTNode.TYPE.BIN_EXP:
            # 二元表达式需要有两个子节点
            if len(node.children) != 2:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.BINARY_EXPRESSION_ERROR,
                    expression=self.expression,
                    positions=[token.range[0] for token in node.tokens],
                    primary_info=node.tokens[0].value if node.tokens else ""
                )

            # 检查子节点
            self._check_node(node.children[0])
            self._check_node(node.children[1])

        elif node.type == ASTNode.TYPE.URY_EXP:
            # 一元表达式需要有一个子节点
            if len(node.children) != 1:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.UNARY_EXPRESSION_ERROR,
                    expression=self.expression,
                    positions=[token.range[0] for token in node.tokens],
                    primary_info=node.tokens[0].value if node.tokens else ""
                )

            # 检查子节点
            self._check_node(node.children[0])

        elif node.type == ASTNode.TYPE.FUN_CAL:
            # 检查函数调用
            func_name = node.tokens[0].value
            expected_param_count = self._get_expected_param_count(func_name)

            if expected_param_count != -1 and len(node.children) != expected_param_count:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.FUNCTION_PARAM_COUNT_ERROR,
                    expression=self.expression,
                    positions=[pos for token in node.tokens for pos in (
                        range(token.range[0], token.range[1] + 1) if token.type == Token.TYPE.FUNCTION else [token.range[0]])],
                    primary_info=func_name,
                    secondary_info=f"Expected {expected_param_count} parameters, got {len(node.children)}"
                )

            # 检查每个参数
            for child in node.children:
                self._check_node(child)

        elif node.type == ASTNode.TYPE.GRP_EXP:
            # 分组表达式需要有一个子节点
            if len(node.children) != 1:
                raise OlocSyntaxError(
                    exception_type=OlocSyntaxError.TYPE.GROUP_EXPRESSION_ERROR,
                    expression=self.expression,
                    positions=[token.range[0] for token in node.tokens],
                )

            # 检查子节点
            self._check_node(node.children[0])

    def _get_expected_param_count(self, func_name):
        r"""
        获取函数预期的参数数量
        :param func_name: 函数名
        :return: 参数数量，-1表示可变参数
        """
        # 这里需要根据oloc的函数定义提供参数数量信息
        function_param_counts = {
            'pow': 2,
            'sqrt': 1,
            'square': 1,
            'cube': 1,
            'reciprocal': 1,
            'exp': 1,
            'mod': 2,
            'fact': 1,
            'abs': 1,
            'sign': 1,
            'gcd': 2,
            'lcm': 2,
            'sin': 1,
            'cos': 1,
            'tan': 1,
            'cosec': 1,
            'sec': 1,
            'cot': 1,
            'asin': 1,
            'acos': 1,
            'atan': 1,
            'acosec': 1,
            'asec': 1,
            'acot': 1,
            'log': 2,
            'lg': 1,
            'ln': 1
        }

        return function_param_counts.get(func_name, -1)  # -1表示可变参数或未知函数

    def execute(self):
        r"""
        执行语法分析
        :return: None
        """
        start_time = time.time_ns()
        self._static_check()
        self._build()
        self._syntax_check()
        self.time_cost = time.time_ns() - start_time


"""test"""
if __name__ == '__main__':
    import simpsave as ss
    from oloc_preprocessor import Preprocessor

    def run_test():
        tests = ss.read('test_cases', file='./data/oloctest.ini')
        time_costs = []
        err_count = 0
        print('___________')
        for index, test in enumerate(tests):
            # if target_index % 200 == 0:
            #     print("=", end="")
            try:
                preprocessor = Preprocessor(test)
                preprocessor.execute()
                lexer = Lexer(preprocessor.expression)
                lexer.execute()
                parser = Parser(lexer.tokens)
                parser.execute()
                print(test, end="\n=")
                print(preprocessor.expression, end="\n=")
                print(lexer.expression, end="\n=")
                print(parser.expression)
                print(parser.ast)
                time_costs.append(preprocessor.time_cost + lexer.time_cost + parser.time_cost)
            except IndexError as ie:
                raise ie
            except Exception as e:
                print(e)
                err_count += 1
        print(f"\n"
              f"Avg Time Cost For {len(time_costs)} cases ({err_count} skip): {sum(time_costs) / len(time_costs) / 1000000} ms\n"
              )

    run_test()

    while True:
        expression = input(">>")
        preprocessor = Preprocessor(expression)
        preprocessor.execute()
        lexer = Lexer(preprocessor.expression)
        lexer.execute()
        parser = Parser(lexer.tokens)
        parser.execute()
        ast = parser.ast
        print(ast)
        print(preprocessor.time_cost + lexer.time_cost + parser.time_cost)

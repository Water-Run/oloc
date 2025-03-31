r"""
:author: WaterRun
:date: 2025-03-31
:file: oloc_parser.py
:description: Oloc parser
"""

import time

import oloc_utils as utils
from oloc_lexer import Lexer
from oloc_token import Token
from oloc_exceptions import *


class Unit:
    r"""
    运算体单元
    """

    class TYPE(Enum):
        r"""
        运算体单元类型
        """
        BIN_EXP = 'BinaryExpression'
        LITERAL = 'Literal'
        FUN_CAL = 'FunctionCall'
        GRP_EXP = 'GroupExpression'

    def __init__(self, unit_type: TYPE, token_flow=list[Token]):
        self.type = unit_type
        self.flow = token_flow
        self.sub: list[Unit] = []

    def __repr__(self):
        result = (f"Unit: {self.type}\n"
                  f"{self.flow}\n"
                  f"{len(self.sub)} sub(s): ")
        for index, temp_sub in self.sub:
            result += f"Sub {index}: "
            result += str(temp_sub)
        return result


class Parser:
    r"""
    语法分析器
    :param tokens: 用于构造的Token流
    """

    def __init__(self, tokens: list[Token]):
        self.tokens, self.expression = Lexer.update(tokens)
        self.units: list[Unit] = []
        self.time_cost = -1

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
        VALID_NUMBERS = (
            Token.TYPE.INTEGER,
            Token.TYPE.LONG_CUSTOM,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.NATIVE_IRRATIONAL,
        )

        absolute_symbol_waiting_right = False
        absolute_symbol_current_index = -1

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

                        absolute_symbol_waiting_right = not absolute_symbol_waiting_right
                        absolute_symbol_current_index = token_index

                        if token_index != len(self.tokens) - 1 and self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('°', '!', '|'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if token_index > 0 and self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('*', '/', '°', '%', '!', '|'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                    case "√" | "+" | "-":

                        if not token_index != len(self.tokens) - 1:
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('*', '/', '°', '^', '%', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                    case "!" | "°":

                        if not token_index > 0:
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                    case  "*" | "/" | "^" | "%":

                        if token_index not in range(1, len(self.tokens) - 1):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
                                expression=self.expression,
                                positions=list(range(*temp_token.range)),
                                primary_info=temp_token.value,
                            )

                        if self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and \
                                self.tokens[token_index + 1].value in ('*', '/', '°', '^', '%', '!'):
                            raise OlocSyntaxError(
                                exception_type=OlocSyntaxError.TYPE.OPERATOR_MISPLACEMENT,
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

                if (token_index - 1 >= 0 and self.tokens[token_index - 1].type not in (Token.TYPE.LBRACKET, Token.TYPE.OPERATOR, Token.TYPE.PARAM_SEPARATOR)) or \
                        (token_index + 1 == len(self.tokens) or self.tokens[token_index + 1].type != Token.TYPE.LBRACKET):
                    raise OlocSyntaxError(
                        exception_type=OlocSyntaxError.TYPE.FUNCTION_MISPLACEMENT,
                        expression=self.expression,
                        positions=list(range(*temp_token.range)),
                        primary_info=temp_token.value,
                    )

            # 函数分隔符检查
            if temp_token.type == Token.TYPE.PARAM_SEPARATOR:
                if (token_index not in range(1, len(self.tokens) - 1)) \
                        or (self.tokens[token_index - 1].type == Token.TYPE.LBRACKET)\
                        or (self.tokens[token_index + 1].type == Token.TYPE.RBRACKET)\
                        or (self.tokens[token_index - 1].type == Token.TYPE.OPERATOR and self.tokens[token_index - 1].value in ('+', '-', '*', '/', '√', '^', '%'))\
                        or (self.tokens[token_index + 1].type == Token.TYPE.OPERATOR and self.tokens[token_index + 1].value in ('*', '/', '^', '%')):
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

        if absolute_symbol_waiting_right:
            raise OlocSyntaxError(
                exception_type=OlocSyntaxError.TYPE.ABSOLUTE_SYMBOL_MISMATCH,
                expression=self.expression,
                positions=[absolute_symbol_current_index],
                primary_info="|",
            )

    def _build(self):
        r"""
        生成Unit流
        :return: None
        """
        LITERAL = (
            Token.TYPE.INTEGER,
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.LONG_CUSTOM,
        )
        for token_index, temp_token in enumerate(self.tokens):
            ...

    def _syntax_check(self):
        r"""
        语法检查
        :return: None
        """

    def execute(self):
        r"""
        执行语法分析
        :return: None
        """
        start_time = time.time_ns()
        self._static_check()
        # self._build()
        # self._syntax_check()
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
                print(test, end=" => ")
                for token in parser.tokens:
                    print(token.value, end=" ")
                print("")
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
        print(parser.tokens)
        print(preprocessor.time_cost + lexer.time_cost + parser.time_cost)

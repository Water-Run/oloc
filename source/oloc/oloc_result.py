r"""
:author: WaterRun
:date: 2025-04-08
:file: oloc_result.py
:description: Oloc result
"""

import time

from typing import Any
from fractions import Fraction

from oloc_token import Token
from oloc_exceptions import *
from oloc_preprocessor import Preprocessor
from oloc_lexer import Lexer
from oloc_parser import Parser
from oloc_evaluator import Evaluator

import oloc_utils as utils


def output_filter(tokens: list[Token]) -> str:
    r"""
    格式化过滤Token流并输出
    :param tokens: 待过滤输出的token流
    :return: 过滤后的生成的表达式字符串
    """

    def _add_separator(num: Token, separator: str, thresholds: int, interval: int) -> str:
        r"""
        添加数字分隔符
        :param num: 待添加的数字（Token 类型，需要有 num.value 属性）
        :param separator: 分隔符形式
        :param thresholds: 分隔符阈值（大于该值才添加分隔符）
        :param interval: 分隔符间隔（每隔 interval 个字符插入一个分隔符）
        :return: 添加分隔符后的字符串数字
        """
        # 如果数字长度小于等于阈值，直接返回原始值
        if len(num.value) <= thresholds:
            return num.value

        # 倒序插入分隔符（从右向左操作）
        reversed_num = num.value[::-1]  # 将字符串数字反转
        parts = [
            reversed_num[i:i + interval] for i in range(0, len(reversed_num), interval)
        ]  # 按间隔切分为块
        after_add = separator.join(parts)  # 使用分隔符连接
        return after_add[::-1]  # 再次反转回原始顺序

    configs = utils.get_formatting_output_function_options_table()

    between_token = " " * configs["readability"]["space between tokens"]
    number_seperator = "_" if configs["custom"]["underline-style number separator"] else ","

    ascii_native_irrational_map = {"π": "pi", "𝑒": "e"}
    superscript_map = {'1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
                       '0': '⁰'}

    result = ""
    add_superscript = False

    # 字符串处理
    for index, temp_token in enumerate(tokens):

        if temp_token.type != Token.TYPE.INTEGER:
            add_superscript = False
        if configs["readability"]["superscript"] and temp_token.type == Token.TYPE.OPERATOR and temp_token.value == "^":
            add_superscript = True
            continue

        if 1 <= index <= len(tokens) - 1 and configs["custom"]["omit the multiplication sign"] and \
                temp_token.type == Token.TYPE.OPERATOR and temp_token.value == '*' and \
                Lexer.omit_multiplication_sign_condition(tokens[index - 1], tokens[index + 1]):
            continue

        # 当不启用保留无理数参数时,舍弃无理数参数
        if temp_token.type == Token.TYPE.IRRATIONAL_PARAM and not configs["custom"]["retain irrational param"]:
            continue

        elif temp_token.type == Token.TYPE.NATIVE_IRRATIONAL and configs["custom"][
            "non-ascii character form native irrational"]:
            result += ascii_native_irrational_map[temp_token.value]

        elif temp_token.type == Token.TYPE.INTEGER:
            if add_superscript:
                for char in temp_token.value:
                    result += superscript_map[char]
                    continue
            else:
                result += _add_separator(temp_token, number_seperator,
                                     configs["readability"]["number separators add thresholds"],
                                     configs["readability"]["number separator interval"])
        else:
            result += temp_token.value

        if index != len(tokens) - 1 and \
                not (configs["readability"]["superscript"] and tokens[index + 1].value == '^') and\
                not (configs["custom"]["omit the multiplication sign"] and tokens[index + 1].value == '*' and index + 2 < len(tokens) and Lexer.omit_multiplication_sign_condition(tokens[index], tokens[index + 2])):
            result += between_token

    return result


class OlocResult:
    r"""
    表达oloc计算结果的类，具有不可变性。
    一旦实例化,OlocResult 的属性无法修改或删除。

    :param expression: 要计算的原始表达式
    :param preprocessor: 构造结果的预处理器
    :param lexer: 构造结果的词法分析器
    :param parser: 构造结构的语法分析器
    :param evaluator: 构造结果的求值器
    """

    def __init__(self, expression: str, preprocessor: Preprocessor, lexer: Lexer, parser: Parser, evaluator: Evaluator):

        start = time.time_ns()

        self._expression = expression
        self._preprocessor = preprocessor
        self._lexer = lexer
        self._parser = parser
        self._evaluator = evaluator

        self._result: list[str] = []

        for tokens in self._evaluator.result:
            self._result.append(output_filter(tokens))

        self._version = utils.get_version()

        self._result_time_cost = time.time_ns() - start
        self._time_cost = self._preprocessor.time_cost + self._lexer.time_cost + self._parser.time_cost + self._evaluator.time_cost + self._result_time_cost

        self._detail: dict[any] = {
            "expression": {
                "input": self._expression,
                "preprocessor": self._preprocessor.expression,
                "lexer": self._lexer.expression,
                "parser": self._parser.expression,
                "evaluator": self._evaluator.expression,
            },
            "token flow": {
                "lexer": self._lexer.tokens,
                "parser": self._parser.tokens,
                "evaluator": self._evaluator.tokens,
            },
            "ast": {
                "parser": self._parser.ast,
                "evaluator": self._evaluator.ast,
            },
            "time cost": {
                "preprocessor": self._preprocessor.time_cost,
                "lexer": self._lexer.time_cost,
                "parser": self._parser.time_cost,
                "evaluator": self._evaluator.time_cost,
                "result": self._result_time_cost
            },
            "result": self._result,
            "version": self._version,
        }

    def format_detail(self, simp: bool = True) -> str:
        r"""
        获取格式化计算细节
        :param simp: 是否返回简化模式结果
        :return: 格式化计算细节字符串
        """

        # 定义子函数
        def _format_simple() -> str:
            r"""
            生成简化版的计算细节
            :return: 简化模式的计算细节字符串
            """
            result = f"{self._expression}\n={self._parser.expression}\n"
            for temp_result in self._result:
                result += f"={temp_result}\n"
            result += f"In {self._time_cost / 1000000:.6f} ms"
            return result

        def _format_summary() -> str:
            r"""
            生成摘要部分
            :return: 格式化后的摘要字符串
            """
            result = "== Summary ==\n"
            result += f"Input Expression: {self._detail['expression']['input']}\n"
            result += f"Final Result    : {self._detail['expression']['evaluator']}\n"
            result += f"Total Time      : {self._time_cost / 1000000:.6f} ms\n"
            result += f"Steps Token     : {len(self._result)}\n\n"
            return result

        def _format_expression_flow() -> str:
            r"""
            生成表达式变化过程
            :return: 格式化后的表达式流程字符串
            """
            result = "== Expression Flow ==\n"
            result += f"Input       : {self._detail['expression']['input']}\n"
            result += f"Preprocessor: {self._detail['expression']['preprocessor']}\n"
            result += f"Lexer       : {self._detail['expression']['lexer']}\n"
            result += f"Parser      : {self._detail['expression']['parser']}\n"
            result += f"Evaluator   : {self._detail['expression']['evaluator']}\n\n"
            return result

        def _format_token_flow() -> str:
            r"""
            生成Token流信息
            :return: 格式化后的Token流字符串
            """
            result = "== Token Flow ==\n"
            result += "Lexer Tokens:\n"
            for i, token in enumerate(self._detail['token flow']['lexer']):
                result += f"  [{i}] {token}\n"

            result += "\nParser Tokens:\n"
            for i, token in enumerate(self._detail['token flow']['parser']):
                result += f"  [{i}] {token}\n"

            result += "\nEvaluator Tokens:\n"
            for i, token in enumerate(self._detail['token flow']['evaluator']):
                result += f"  [{i}] {token}\n"
            return result

        def _format_ast() -> str:
            r"""
            生成AST信息
            :return: 格式化后的AST字符串
            """
            result = "\n== Abstract Syntax Tree ==\n"
            result += f"{self._detail['ast']['parser']}\n\n"
            return result

        def _format_evaluation_process() -> str:
            r"""
            生成计算过程
            :return: 格式化后的计算过程字符串
            """
            result = "== Evaluation Process ==\n"
            for i, step in enumerate(self._result):
                if i == 0:
                    result += f"Initial: {step}\n"
                else:
                    result += f"Step {i}: {step}\n"
            result += f"Final: {self._detail['expression']['evaluator']}\n\n"
            return result

        def _format_complexity_analysis() -> str:
            r"""
            生成表达式复杂度分析
            :return: 格式化后的复杂度分析字符串
            """
            tokens = self._detail['token flow']['lexer']

            # 定义各类型的权重
            weights = {
                # 基本数字类型
                Token.TYPE.INTEGER: 1,
                Token.TYPE.FINITE_DECIMAL: 1.5,
                Token.TYPE.PERCENTAGE: 2,
                Token.TYPE.INFINITE_DECIMAL: 2.5,

                # 无理数类型
                Token.TYPE.NATIVE_IRRATIONAL: 2,
                Token.TYPE.SHORT_CUSTOM: 2.5,
                Token.TYPE.LONG_CUSTOM: 3,
                Token.TYPE.IRRATIONAL_PARAM: 0,

                # 运算符
                Token.TYPE.OPERATOR: 1.5,
                Token.TYPE.LBRACKET: 1,
                Token.TYPE.RBRACKET: 1,

                # 函数和分隔符
                Token.TYPE.FUNCTION: 5,
                Token.TYPE.PARAM_SEPARATOR: 0.5,

                # 其他
                Token.TYPE.UNKNOWN: 10
            }

            # 按类型统计token数量
            type_counts = {}
            for token in tokens:
                token_type = token.type
                if token_type not in type_counts:
                    type_counts[token_type] = 0
                type_counts[token_type] += 1

            # 计算总复杂度分数
            complexity_score = 0
            for token_type, count in type_counts.items():
                if token_type in weights:
                    complexity_score += weights[token_type] * count

            # 嵌套深度分析
            bracket_stack = []
            max_depth = 0
            current_depth = 0

            for token in tokens:
                if token.type == Token.TYPE.LBRACKET:
                    bracket_stack.append(token.value)
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif token.type == Token.TYPE.RBRACKET:
                    if bracket_stack:  # 检查栈是否为空
                        bracket_stack.pop()
                        current_depth -= 1

            # 函数嵌套分析
            function_count = 0
            function_depth = 0
            max_function_depth = 0

            for i, token in enumerate(tokens):
                if token.type == Token.TYPE.FUNCTION:
                    function_count += 1
                    # 查找下一个括号，分析是否是函数嵌套
                    if i + 1 < len(tokens) and tokens[i + 1].type == Token.TYPE.LBRACKET:
                        function_depth += 1
                        max_function_depth = max(max_function_depth, function_depth)

                        # 查找对应的右括号
                        bracket_count = 1
                        for j in range(i + 2, len(tokens)):
                            if tokens[j].type == Token.TYPE.LBRACKET:
                                bracket_count += 1
                            elif tokens[j].type == Token.TYPE.RBRACKET:
                                bracket_count -= 1
                                if bracket_count == 0:
                                    if j + 1 < len(tokens) and tokens[j + 1].type != Token.TYPE.FUNCTION:
                                        function_depth -= 1
                                    break

            # 为嵌套深度添加额外分数
            complexity_score += max_depth * 2
            complexity_score += max_function_depth * 3

            # 根据总分确定复杂度级别
            complexity_level = ""
            if complexity_score <= 10:
                complexity_level = "Very Simple"
            elif complexity_score <= 20:
                complexity_level = "Simple"
            elif complexity_score <= 35:
                complexity_level = "Moderate"
            elif complexity_score <= 50:
                complexity_level = "Complex"
            elif complexity_score <= 70:
                complexity_level = "Very Complex"
            else:
                complexity_level = "Extremely Complex"

            # 格式化输出
            result = "== Complexity Analysis ==\n"
            result += f"Overall Complexity: {complexity_level} (Score: {complexity_score:.1f})\n\n"

            # 细节分析
            result += "Token Distribution:\n"
            for token_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                if token_type in weights:
                    token_weight = weights[token_type]
                    token_contribution = token_weight * count
                    token_percentage = (token_contribution / complexity_score) * 100 if complexity_score > 0 else 0
                    result += f"  {token_type}: {count} tokens × {token_weight:.1f} weight = {token_contribution:.1f} ({token_percentage:.1f}%)\n"

            result += f"\nNesting Analysis:\n"
            result += f"  Maximum Bracket Depth: {max_depth}\n"
            result += f"  Function Count: {function_count}\n"
            result += f"  Maximum Function Nesting: {max_function_depth}\n\n"

            # 提供复杂度减少建议
            suggestions = []
            if complexity_score > 20:
                if max_depth > 3:
                    suggestions.append("  • Consider breaking deeply nested expressions into smaller parts")

                if max_function_depth > 2:
                    suggestions.append("  • Reduce function nesting by storing intermediate function results")

                if Token.TYPE.INFINITE_DECIMAL in type_counts and type_counts[Token.TYPE.INFINITE_DECIMAL] > 1:
                    suggestions.append("  • Consider simplifying or approximating infinite decimals")

                if Token.TYPE.LONG_CUSTOM in type_counts:
                    suggestions.append("  • Use shorter variable names for custom irrational numbers")

                if len(tokens) > 30:
                    suggestions.append("  • Split long expressions into multiple calculations")

            # 仅在有建议时显示标题和建议
            if suggestions:
                result += "Complexity Reduction Suggestions:\n"
                result += "\n".join(suggestions) + "\n"

            return result

        def _format_time_cost() -> str:
            r"""
            生成时间消耗分析
            :return: 格式化后的时间消耗字符串
            """
            # 提取各阶段时间
            preproc_time = self._detail['time cost']['preprocessor'] / 1000000
            lexer_time = self._detail['time cost']['lexer'] / 1000000
            parser_time = self._detail['time cost']['parser'] / 1000000
            evaluator_time = self._detail['time cost']['evaluator'] / 1000000
            result_time = self._detail['time cost']['result'] / 1000000
            total_time = self._time_cost / 1000000

            result = "\n== Time Cost (ms) ==\n"
            result += f"Preprocessor: {preproc_time:.6f} ms\n"
            result += f"Lexer       : {lexer_time:.6f} ms\n"
            result += f"Parser      : {parser_time:.6f} ms\n"
            result += f"Evaluator   : {evaluator_time:.6f} ms\n"
            result += f"Result      : {result_time:.6f} ms\n"
            result += f"Total       : {total_time:.6f} ms\n\n"

            # 添加横条可视化
            if total_time > 0:
                # 计算百分比
                preproc_pct = (preproc_time / total_time) * 100
                lexer_pct = (lexer_time / total_time) * 100
                parser_pct = (parser_time / total_time) * 100
                evaluator_pct = (evaluator_time / total_time) * 100
                result_pct = (result_time / total_time) * 100

                # 创建可视化横条
                result += _format_time_bar(
                    preproc_pct, lexer_pct, parser_pct, evaluator_pct, result_pct
                )

            return result

        def _format_time_bar(preproc_pct, lexer_pct, parser_pct, evaluator_pct, result_pct) -> str:
            r"""
            生成时间分布横条可视化
            :param preproc_pct: 预处理器所占百分比
            :param lexer_pct: 词法分析器所占百分比
            :param parser_pct: 语法分析器所占百分比
            :param evaluator_pct: 求值器所占百分比
            :param result_pct: 结果处理所占百分比
            :return: 格式化后的时间分布横条字符串
            """
            bar_width = 60  # 横条总宽度

            # 计算每个部分的字符数
            preproc_width = max(1, int(preproc_pct * bar_width / 100)) if preproc_pct > 0 else 0
            lexer_width = max(1, int(lexer_pct * bar_width / 100)) if lexer_pct > 0 else 0
            parser_width = max(1, int(parser_pct * bar_width / 100)) if parser_pct > 0 else 0
            evaluator_width = max(1, int(evaluator_pct * bar_width / 100)) if evaluator_pct > 0 else 0
            result_width = max(1, int(result_pct * bar_width / 100)) if result_pct > 0 else 0

            # 调整总宽度
            total_width = preproc_width + lexer_width + parser_width + evaluator_width + result_width

            # 处理舍入误差
            if total_width < bar_width:
                # 将差值添加到最大部分
                diff = bar_width - total_width
                max_pct = max(preproc_pct, lexer_pct, parser_pct, evaluator_pct, result_pct)

                if max_pct == preproc_pct and preproc_width > 0:
                    preproc_width += diff
                elif max_pct == lexer_pct and lexer_width > 0:
                    lexer_width += diff
                elif max_pct == parser_pct and parser_width > 0:
                    parser_width += diff
                elif max_pct == evaluator_pct and evaluator_width > 0:
                    evaluator_width += diff
                elif result_width > 0:
                    result_width += diff
            elif total_width > bar_width:
                # 从最大部分减去差值
                diff = total_width - bar_width
                max_width = max(preproc_width, lexer_width, parser_width, evaluator_width, result_width)

                if max_width == preproc_width and preproc_width > diff:
                    preproc_width -= diff
                elif max_width == lexer_width and lexer_width > diff:
                    lexer_width -= diff
                elif max_width == parser_width and parser_width > diff:
                    parser_width -= diff
                elif max_width == evaluator_width and evaluator_width > diff:
                    evaluator_width -= diff
                elif result_width > diff:
                    result_width -= diff

            # 生成横条
            result = "Time Distribution:\n"

            # 上边界
            result += "+" + "-" * bar_width + "+\n"

            # 横条内容
            bar = "|"
            if preproc_width > 0:
                bar += "P" * preproc_width
            if lexer_width > 0:
                bar += "L" * lexer_width
            if parser_width > 0:
                bar += "A" * parser_width
            if evaluator_width > 0:
                bar += "E" * evaluator_width
            if result_width > 0:
                bar += "R" * result_width
            bar += "|\n"

            result += bar

            # 下边界
            result += "+" + "-" * bar_width + "+\n"

            # 图例
            result += "Legend: P=Preprocessor, L=Lexer, A=Parser, E=Evaluator, R=Result\n"

            # 各部分百分比
            result += f"Preprocessor: {preproc_pct:.1f}%, "
            result += f"Lexer: {lexer_pct:.1f}%, "
            result += f"Parser: {parser_pct:.1f}%, "
            result += f"Evaluator: {evaluator_pct:.1f}%, "
            result += f"Result: {result_pct:.1f}%\n"

            return result

        # 根据 simp 参数选择返回简化或详细版本
        if simp:
            return _format_simple()
        else:
            # 创建详细的计算过程展示
            result = "=== Oloc Calculation Detailed Report ===\n"
            result += f"Version: {self._version}\n\n"

            # 添加各个详细部分
            result += _format_summary()
            result += _format_expression_flow()
            result += _format_token_flow()
            result += _format_ast()
            result += _format_evaluation_process()
            result += _format_complexity_analysis()
            result += _format_time_cost()

            return result

    @property
    def expression(self) -> str:
        r"""
        获取表达式字符串。
        :return: 表达式字符串
        """
        return self._expression

    @property
    def result(self) -> List[str]:
        r"""
        获取表达式计算结果的字符串列表。
        :return: 结果字符串列表
        """
        return self._result

    @property
    def time_cost(self) -> float:
        r"""
        获取总计算耗时
        :return: 计算耗时(ms)
        """
        return self._time_cost

    @property
    def detail(self) -> dict:
        r"""
        获取计算细节
        :return: 计算细节字典
        """
        return self._detail

    def __str__(self) -> str:
        r"""
        将 OlocResult 转换为字符串，返回 result 列表的最后一项。
        :return: result 列表的最后一项。如果列表为空，返回空字符串
        """
        return self._result[-1] if self._result else ""

    def __repr__(self) -> str:
        r"""
        返回 OlocResult 对象的字符串表示形式。
        :return: 对象的字符串表示形式
        """
        return f"OlocResult({self._expression} => {self._result[-1]}; {self.time_cost / 1_000_000} ms)"

    def __float__(self) -> float:
        r"""
        转换为浮点型。
        :raises OlocConversionError: 如果无法进行转换(如缺失无理数参数的无理数)
        :return: 转化后的浮点数
        """

    def __int__(self) -> int:
        r"""
        转换为整型。(先转化为浮点)
        :return: 转化后的整数
        """
        return int(self.__float__())

    def get_fraction(self) -> Fraction:
        r"""
        转化为Python原生的Fraction类型。(先转化为浮点)
        :return: Fraction类型的结果
        """

    def __setattr__(self, name: str, value: Any) -> None:
        r"""
        禁止修改 OlocResult 的属性。
        :raises AttributeError: 如果尝试修改已存在的属性
        """
        if hasattr(self, name):
            raise AttributeError(f"OlocResult is immutable. Cannot modify attribute '{name}'.")
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        r"""
        禁止删除 OlocResult 的属性。
        :raises AttributeError: 如果尝试删除属性
        """
        raise AttributeError(f"OlocResult is immutable. Cannot delete attribute '{name}'.")


"""test"""
if __name__ == "__main__":
    ...

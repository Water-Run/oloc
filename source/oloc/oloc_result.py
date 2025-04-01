r"""
:author: WaterRun
:date: 2025-04-01
:file: oloc_result.py
:description: Oloc result
"""
from typing import Any
from fractions import Fraction
from oloc_token import Token
from oloc_exceptions import *
import oloc_utils as utils


def output_filter(tokens: list[Token]) -> str:
    r"""
    格式化过滤Token流并输出
    :param tokens: 待过滤输出的token流
    :return: 过滤后的生成的表达式字符串
    """
    configs = utils.get_formatting_output_function_options_table()

    between_token = " " * configs["readability"]["space between token"]
    number_seperator = "," if configs["custom"]["underline-style number separator"] else "_"
    ascii_native_irrational_map = {"π": "pi", "𝑒": "e"}

    result = ""

    def _add_separator(num: Token, seperator: str, thresholds: int, interval: int) -> list[Token]:
        r"""
        添加数字分隔符
        :param num: 待添加的数字
        :param seperator: 分隔符形式
        :param thresholds: 分隔符阈值
        :param interval: 分隔符间隔
        :return: 添加后的分隔符列表
        """
        after_add = []
        return after_add

    # 字符串处理
    for index, temp_token in enumerate(tokens):

        # 当不启用保留无理数参数时,舍弃无理数参数
        if temp_token.type == Token.TYPE.IRRATIONAL_PARAM and not configs["retain irrational param"]:
            continue

        if temp_token.type == Token.TYPE.NATIVE_IRRATIONAL and configs["custom"]["non-ascii character form native irrational"]:
            result += ascii_native_irrational_map[temp_token.value]

        # 添加Token间隔空格
        if len(tokens) > 1 and index != len(tokens) - 1:
            result += between_token

    return result


class OlocResult:
    r"""
    表达oloc计算结果的类，具有不可变性。
    一旦实例化,OlocResult 的属性无法修改或删除。

    :param expression: 要计算的原始表达式
    :param token_flows: 表达式计算结果的Token流列表
    :raises TypeError: 如果输入的参数类型不正确
    """

    def __init__(self, expression: str, token_flows: list[list[Token]]) -> None:
        self._expression = expression
        self._flows = token_flows
        self._result: list[str] = []
        for tokens in self._flows:
            self.result.append(output_filter(tokens))
        self._raw_result: str | None = None

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
        return f"OlocResult(expression={self._expression!r}, result={self._result!r})"

    def __float__(self) -> float:
        r"""
        转换为浮点型。
        :raises OlocConversionError: 如果无法进行转换(如缺失无理数参数的无理数)
        :return: 转化后的浮点数
        """

        IRRATIONALS = (
            Token.TYPE.NATIVE_IRRATIONAL,
            Token.TYPE.SHORT_CUSTOM,
            Token.TYPE.LONG_CUSTOM,
        )

        class IrrUnit:
            r"""
            含参无理数单元
            :param irr_token: 构造的无理数Token单元
            :param param_token: 构造的无理数参数Token单元
            :param expression: 结果表达式
            """

            def __init__(self, irr_token: Token, param_token: Token, expression: str):
                self.irr = irr_token
                self.param = param_token
                self.expression = expression
                self.value = self._parse_param()

            def _parse_param(self) -> float:
                r"""
                解析无理数参数并返回处理后的结果

                对于原生无理数,使用高精度算法计算π和e的值，可以实现任意精度（受限于系统资源）。
                对于π，使用Bailey–Borwein–Plouffe公式
                对于e，使用泰勒级数展开

                :raise OlocConversionError: 如果参数不合法
                :return: 解析后的结果
                """
                if self.irr.type == Token.TYPE.NATIVE_IRRATIONAL:
                    if not self.param.value.replace("?", "").isdigit():
                        raise OlocConversionError(
                            exception_type=OlocConversionError.TYPE.NATIVE_PARAM,
                            expression=self.expression,
                            positions=[*range(self.irr.range[0], self.irr.range[1] + 1),
                                       *range(self.param.range[0], self.param.range[1] + 1)],
                            primary_info=self.irr.value,
                            secondary_info=self.param.value,
                        )

                    from decimal import Decimal, getcontext

                    retain_places = int(self.param.value.replace("?", ""))
                    # 设置额外精度以确保四舍五入的准确性
                    working_precision = retain_places + 10
                    getcontext().prec = working_precision

                    if self.irr.value == "π":
                        # 使用Bailey–Borwein–Plouffe公式计算π
                        pi = Decimal(0)
                        k = 0
                        # BBP公式可以直接计算π的任意位
                        while k < working_precision:
                            term = (Decimal(1) / (16 ** k)) * (
                                    Decimal(4) / (8 * k + 1) -
                                    Decimal(2) / (8 * k + 4) -
                                    Decimal(1) / (8 * k + 5) -
                                    Decimal(1) / (8 * k + 6)
                            )
                            pi += term
                            if term < Decimal(10) ** (-working_precision):
                                break
                            k += 1

                        # 转换为字符串保持精度，然后四舍五入到所需位数
                        pi_str = str(pi)
                        decimal_point = pi_str.find('.')
                        if decimal_point != -1:
                            integer_part = pi_str[:decimal_point]
                            decimal_part = pi_str[decimal_point + 1:]
                            if len(decimal_part) > retain_places:
                                # 手动四舍五入
                                if int(decimal_part[retain_places]) >= 5:
                                    # 创建一个只有保留位数的小数部分
                                    rounded_decimal = str(int(decimal_part[:retain_places]) + 1)
                                    # 处理进位
                                    if len(rounded_decimal) > retain_places:
                                        integer_part = str(int(integer_part) + 1)
                                        rounded_decimal = rounded_decimal[1:]
                                else:
                                    rounded_decimal = decimal_part[:retain_places]

                                return float(f"{integer_part}.{rounded_decimal}")

                        return float(pi)

                    else:  # 假设为 "e"
                        # 使用泰勒级数计算e
                        e = Decimal(1)
                        factorial = Decimal(1)
                        k = 1

                        # 当项变得足够小时停止
                        while True:
                            factorial *= k
                            term = Decimal(1) / factorial
                            e += term
                            if term < Decimal(10) ** (-working_precision):
                                break
                            k += 1

                        # 转换为字符串保持精度，然后四舍五入到所需位数
                        e_str = str(e)
                        decimal_point = e_str.find('.')
                        if decimal_point != -1:
                            integer_part = e_str[:decimal_point]
                            decimal_part = e_str[decimal_point + 1:]
                            if len(decimal_part) > retain_places:
                                # 手动四舍五入
                                if int(decimal_part[retain_places]) >= 5:
                                    # 创建一个只有保留位数的小数部分
                                    rounded_decimal = str(int(decimal_part[:retain_places]) + 1)
                                    # 处理进位
                                    if len(rounded_decimal) > retain_places:
                                        integer_part = str(int(integer_part) + 1)
                                        rounded_decimal = rounded_decimal[1:]
                                else:
                                    rounded_decimal = decimal_part[:retain_places]

                                return float(f"{integer_part}.{rounded_decimal}")

                        return float(e)
                else:
                    ...

        for token_index, token in enumerate(self._flows[-1]):
            if token.type in IRRATIONALS:
                ...

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

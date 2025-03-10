r"""
:author: WaterRun
:date: 2025-03-10
:file: lexer.py
:description: Oloc lexer
"""

from enum import Enum
import utils


class Token:
    r"""
    表达式中的词元
    :param token_type: 词元的类别
    :param token_range: 词元在表达式中的范围(位置)
    :param token_value: 词元的实际值
    """

    class TYPE(Enum):
        r"""
        枚举词原的所有类型
        """
        # 数字类型
        PERCENTAGE = 'percentage'            # 百分数: 100%
        MIXED_FRACTION = 'mixed fraction'    # 带分数: 3\1/2
        INFINITE_DECIMAL = 'infinite recurring decimal'  # 无限小数: 3.3... 或 2.3:4
        FINITE_DECIMAL = 'finite decimal'    # 有限小数: 3.14
        INTEGER = 'integer'                  # 整数: 42
        FRACTION = 'fraction'                # 分数: 1/2

        # 无理数类型
        NATIVE_IRRATIONAL = 'native irrational number'  # 原生无理数: π, e
        SHORT_CUSTOM = 'short custom irrational'        # 短自定义无理数: x, y
        LONG_CUSTOM = 'long custom irrational'          # 长自定义无理数: <name>

        # 运算符
        OPERATOR = 'operator'                # 运算符: +, -, *, /等

        # 分组符号
        LBRACKET = 'left bracket'            # 左括号: (, [, {
        RBRACKET = 'right bracket'           # 右括号: ), ], }

        # 函数相关
        FUNC = 'function'                    # 函数: sin, cos等
        PARAM_SEPARATOR = 'parameter separator'  # 参数分隔符: ,或;

        # 未知类型
        UNKNOWN = 'unknown'                  # 无法识别的字符

    def __init__(self, token_type: TYPE, token_range: list, token_value: str = None):
        self.type = token_type
        self.range = token_range
        self.value = token_value if token_value is not None else None

    def __repr__(self):
        return f"Token({self.type.value}, {self.range}, '{self.value}')"

    def is_legal(self) -> bool:
        ...


class Lexer:
    r"""
    词法分析器
    :param expression: 待处理的表达式
    """

    def __init__(self, expression: str):
        self.expression = expression

    def execute(self):
        ...

    @staticmethod
    def _is_native_irrational(s: str) -> bool:
        r"""
        判断是否为原生无理数
        :param s: 待检查的字符
        :return: 如果是原生无理数(π或e)则返回True，否则返回False
        """
        return s in ["π", "𝑒"]  # 预处理已将所有变体转换为这些符号

    @staticmethod
    def _is_operator(c: str) -> bool:
        r"""
        判断是否为运算符
        :param c: 待检查的字符
        :return: 如果是运算符则返回True，否则返回False
        """
        # 获取符号表中的运算符
        operators = list(utils.get_symbol_mapping_table().keys())
        # 过滤掉空字符串和括号等非运算符
        operators = [op for op in operators if op and op not in "()[]{}<>"]
        return c in operators

    @staticmethod
    def _is_bracket(c: str) -> bool:
        r"""
        判断是否为括号
        :param c: 待检查的字符
        :return: 如果是括号则返回True，否则返回False
        """
        return c in "()[]{}"

    @staticmethod
    def _is_separator(c: str) -> bool:
        r"""
        判断是否为函数参数分隔符
        :param c: 待检查的字符
        :return: 如果是函数参数分隔符则返回True，否则返回False
        """
        return c in ",;"

    @staticmethod
    def _is_digit(c: str) -> bool:
        r"""
        判断是否为数字字符
        :param c: 待检查的字符
        :return: 如果是数字或小数点则返回True，否则返回False
        """
        return c.isdigit() or c == '.'

    @staticmethod
    def _is_identifier_char(c: str) -> bool:
        r"""
        判断是否为标识符字符
        :param c: 待检查的字符
        :return: 如果是标识符字符(字母、数字或下划线)则返回True，否则返回False
        """
        return c.isalnum() or c == '_'

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :return: 分词后的Token列表
        """

    @staticmethod
    def tokenizer(expression: str) -> list[Token]:
        r"""
        分词器
        :param expression: 待分词的表达式
        :return: 分词后的Token列表
        """
        tokens = []
        i = 0
        function_names = utils.get_function_name_list()

        while i < len(expression):
            # 跳过空白字符
            if expression[i].isspace():
                i += 1
                continue

            # 处理数字(整数、小数、分数、百分数等)
            if expression[i].isdigit() or (expression[i] == '.' and i+1 < len(expression) and expression[i+1].isdigit()):
                start = i
                decimal_point = False
                percentage = False
                fraction = False
                mixed_fraction = False
                infinite = False

                # 处理数字部分
                while i < len(expression):
                    # 整数部分
                    if expression[i].isdigit():
                        i += 1
                    # 处理小数点
                    elif expression[i] == '.' and not decimal_point:
                        decimal_point = True
                        i += 1
                    # 处理分数
                    elif expression[i] == '/' and not fraction:
                        # 确保前面有数字
                        if i > start:
                            fraction = True
                            i += 1
                        else:
                            break
                    # 处理带分数
                    elif expression[i] == '\\' and not mixed_fraction:
                        # 确保前面有数字，后面有分数
                        if i > start and i+1 < len(expression) and (expression[i+1].isdigit() or expression[i+1] == '-'):
                            mixed_fraction = True
                            i += 1
                        else:
                            break
                    # 处理显式循环小数部分
                    elif expression[i] == ':' and decimal_point:
                        infinite = True
                        i += 1
                        # 跳过冒号后的数字，它们是循环部分
                        while i < len(expression) and expression[i].isdigit():
                            i += 1
                        break
                    # 处理省略号(无限循环小数)
                    elif expression[i] == '.' and decimal_point:
                        # 检查是否有至少3个连续的点
                        j = i
                        dot_count = 0
                        while j < len(expression) and expression[j] == '.':
                            dot_count += 1
                            j += 1

                        if dot_count >= 3:
                            infinite = True
                            i = j  # 跳过所有点
                            break
                        else:
                            break
                    # 处理百分数
                    elif expression[i] == '%':
                        # 检查后面不是数字或括号，确保这不是模运算符
                        if i+1 >= len(expression) or (not expression[i+1].isdigit() and expression[i+1] not in "([{"):
                            percentage = True
                            i += 1
                        break
                    else:
                        break

                # 根据识别的特征确定数字类型
                token_value = expression[start:i]

                if percentage:
                    token_type = Token.TYPE.PERCENTAGE
                elif mixed_fraction:
                    token_type = Token.TYPE.MIXED_FRACTION
                elif infinite:
                    token_type = Token.TYPE.INFINITE_DECIMAL
                elif decimal_point:
                    token_type = Token.TYPE.FINITE_DECIMAL
                elif fraction:
                    token_type = Token.TYPE.FRACTION
                else:
                    token_type = Token.TYPE.INTEGER

                tokens.append(Token(token_type, [start, i], token_value))
                continue

            # 处理原生无理数(π, e)
            if Lexer._is_native_irrational(expression[i]):
                start = i
                i += 1

                # 检查无理数后的可选问号表达式
                if i < len(expression) and expression[i] == '?':
                    i += 1
                    # 寻找问号后的整数(保留位数)
                    while i < len(expression) and expression[i].isdigit():
                        i += 1

                tokens.append(Token(Token.TYPE.NATIVE_IRRATIONAL, [start, i], expression[start:i]))
                continue

            # 处理自定义长无理数 <name>
            if expression[i] == '<':
                start = i
                i += 1
                # 查找右尖括号
                while i < len(expression) and expression[i] != '>':
                    i += 1

                if i < len(expression) and expression[i] == '>':
                    i += 1

                    # 检查无理数后的可选问号表达式
                    if i < len(expression) and expression[i] == '?':
                        i += 1
                        # 处理问号后的值或符号
                        if i < len(expression) and (expression[i] == '+' or expression[i] == '-'):
                            i += 1
                        else:
                            # 处理小数
                            decimal_seen = False
                            while i < len(expression) and (expression[i].isdigit() or (expression[i] == '.' and not decimal_seen)):
                                if expression[i] == '.':
                                    decimal_seen = True
                                i += 1

                    tokens.append(Token(Token.TYPE.LONG_CUSTOM, [start, i], expression[start:i]))
                    continue

            # 处理函数
            potential_func = ""
            j = i
            while j < len(expression) and Lexer._is_identifier_char(expression[j]):
                potential_func += expression[j]
                j += 1

            if potential_func in function_names and j < len(expression) and expression[j] == '(':
                start = i
                i = j + 1  # 跳过左括号
                tokens.append(Token(Token.TYPE.FUNC, [start, j], potential_func))
                tokens.append(Token(Token.TYPE.LBRACKET, [j, j+1], '('))
                continue

            # 处理自定义短无理数(单个字符)
            if expression[i].isalpha() and not Lexer._is_native_irrational(expression[i]):
                start = i
                i += 1

                # 检查无理数后的可选问号表达式
                if i < len(expression) and expression[i] == '?':
                    i += 1
                    if i < len(expression):
                        if expression[i] in '+-':
                            i += 1
                        else:
                            # 处理小数值
                            decimal_seen = False
                            while i < len(expression) and (expression[i].isdigit() or (expression[i] == '.' and not decimal_seen)):
                                if expression[i] == '.':
                                    decimal_seen = True
                                i += 1

                tokens.append(Token(Token.TYPE.SHORT_CUSTOM, [start, i], expression[start:i]))
                continue

            # 处理运算符
            if Lexer._is_operator(expression[i]):
                start = i

                # 特殊处理可能的多字符运算符
                if expression[i] == '*' and i+1 < len(expression) and expression[i+1] == '*':
                    # 处理 ** 运算符
                    tokens.append(Token(Token.TYPE.OPERATOR, [i, i+2], '**'))
                    i += 2
                elif expression[i] == '%':
                    # 简单处理%符号，后续函数化流程会区分百分比和取余
                    tokens.append(Token(Token.TYPE.OPERATOR, [i, i+1], '%'))
                    i += 1
                else:
                    # 其他单字符运算符
                    tokens.append(Token(Token.TYPE.OPERATOR, [i, i+1], expression[i]))
                    i += 1
                continue

            # 处理括号
            if Lexer._is_bracket(expression[i]):
                start = i
                if expression[i] in '([{':
                    tokens.append(Token(Token.TYPE.LBRACKET, [i, i+1], expression[i]))
                else:
                    tokens.append(Token(Token.TYPE.RBRACKET, [i, i+1], expression[i]))
                i += 1
                continue

            # 处理函数参数分隔符
            if Lexer._is_separator(expression[i]):
                tokens.append(Token(Token.TYPE.PARAM_SEPARATOR, [i, i+1], expression[i]))
                i += 1
                continue

            # 无法识别的字符，归类为UNKNOWN
            start = i
            tokens.append(Token(Token.TYPE.UNKNOWN, [i, i+1], expression[i]))
            i += 1

        return tokens


test_list = [
    # 基础整数测试
    "42",
    "-42",
    "+42",
    "0",

    # 小数测试
    "3.14",
    "-3.14",
    "0.5",
    ".5",  # 省略整数部分的小数
    "10.",  # 省略小数部分的小数

    # 百分数测试
    "50%",
    "-25%",
    "3.14%",
    "0%",

    # 分数测试
    "1/2",
    "-1/2",
    "7/8",
    "0/1",
    "5/-10",  # 分母为负
    "22/7",  # π的近似值

    # 带分数测试
    "3\\1/2",  # 3+1/2 = 7/2
    "-2\\1/4",
    "10\\3/4",
    "0\\1/2",

    # 无限循环小数测试
    "0.333...",
    "1.414...",
    "0.9999...",
    "0.123...",
    "0.142857142857...",  # 1/7的循环小数

    # 显式循环小数测试
    "0.3:3",  # 0.333...
    "1.4:14",  # 1.414141...
    "0.:9",  # 0.999...
    "0.1:42857",  # 1/7 = 0.142857142857...

    # 原生无理数测试
    "π",
    "𝑒",
    "π?3",  # 带精度指示的π
    "𝑒?5",  # 带精度指示的e

    # 短自定义无理数测试
    "x",
    "y",
    "a",
    "z",
    "x?-",  # 负数自定义无理数
    "y?+",  # 正数自定义无理数
    "a?2.5",  # 带值的自定义无理数

    # 长自定义无理数测试
    "<phi>",
    "<黄金分割比>",
    "<root2>",
    "<Pi approximation>",
    "<phi>?1.618",  # 带值的长自定义无理数
    "<negative>?-",  # 负数长自定义无理数
    "<positive>?+",  # 正数长自定义无理数

    # 运算符测试
    "1+2",
    "3-4",
    "5*6",
    "7/8",
    "2^3",
    "2**3",  # 幂运算符的另一种表示
    "10%3",  # 取余运算符
    "5!",  # 阶乘
    "90°",  # 角度符号
    "|x|",  # 绝对值
    "√16",  # 平方根

    # 括号测试
    "(1+2)",
    "[3*4]",
    "{5/6}",
    "((1+2)*(3-4))",
    "[(1+2)*(3+4)]",
    "{(1+2)*[3+4]}",

    # 函数测试
    "sin(π/2)",
    "cos(0)",
    "tan(π/4)",
    "sqrt(16)",
    "log(100)",
    "ln(𝑒)",
    "pow(2,3)",
    "abs(-5)",
    "gcd(12,18)",
    "lcm(4,6)",

    # 函数参数分隔符测试
    "pow(2,3)",
    "pow(2;3)",  # 使用分号作为参数分隔符
    "gcd(12,18)",
    "gcd(12;18)",
    "max(1,2,3,4)",
    "max(1;2;3;4)",

    # 复杂表达式测试
    "1+2*3",
    "(1+2)*3",
    "3*(4+5)/2",
    "sin(π/2)*cos(π/3)",
    "sqrt(2)^2",
    "√(4+5)*(2-1)",
    "2π*r",  # 圆周长公式
    "π*r^2",  # 圆面积公式
    "3\\1/2 + 2\\3/4",  # 带分数加法
    "sin(2π/3)?3 + cos(π/4)?4",  # 带精度指示的函数

    # 混合表达式测试
    "3+4*2/(1-5)^2",
    "3+4*2/(1-5)^2^3",
    "sin(π/2) + cos(π/3) + tan(π/4)",
    "(2.5+1.5)*(3.75-0.75)/(2.25+0.75)",
    "√(a^2+b^2)",  # 勾股定理
    "2πr + 2πh",  # 圆柱表面积
    "a*sin(α) + b*cos(β)",

    # 错误处理测试
    "2++3",  # 连续多个加号
    "4-*5",  # 相连的不兼容运算符
    "6(/7",  # 不匹配的括号
    "8)",  # 缺少左括号
    "sin()",  # 缺少函数参数
    "log(,)",  # 分隔符无参数
    "3,4,5",  # 上下文外的分隔符

    # 易错情况测试
    "2(3+4)",  # 隐式乘法
    "2π",  # 数字与无理数相乘
    "sin(π)cos(0)",  # 函数连乘
    "3.14.15",  # 多个小数点
    "5/6/7",  # 连续分数
    "2//3",  # 连续除号
    "3%",  # 百分号而非取余
    "5%2",  # 取余而非百分号
    "x?-1.5",  # 负数值的无理数

    # 极端情况测试
    "",  # 空字符串
    " ",  # 只有空格
    "1000000000",  # 大整数
    "0.000000001",  # 小小数
    "1/1000000000",  # 小分数
    "999999999/1",  # 大分数
    "999\\999/999",  # 大带分数
    ".5.5.5.5.5.5",  # 多重重复

    # 无理数结合测试
    "π+𝑒",
    "π*𝑒",
    "π/𝑒",
    "π^𝑒",
    "√π",
    "log(𝑒)",
    "sin(π+𝑒)",

    # 复合表达式测试
    "3*(4+5)^2/sin(π/3)",
    "log10(1000)/(2π*√(LC))",
    "(a+b)^2 = a^2 + 2ab + b^2",
    "F = G*m1*m2/r^2",  # 万有引力公式
    "E = mc^2",  # 质能方程
    "PV = nRT",  # 理想气体状态方程
]

for test in test_list:
    print(f"Testing: {test}")
    from preprocessor import Preprocessor
    test_result = Preprocessor(test)
    test_result.execute()
    tokens = Lexer.tokenizer(test_result.expression)
    for token in tokens:
        print(f"  {token}")
    input("Press Enter for next test >>")

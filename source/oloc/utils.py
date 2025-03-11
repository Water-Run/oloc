"""
:author: WaterRun
:date: 2025-03-10
:file: utils.py
:description: Oloc utils
"""

import simpsave as ss


def get_symbol_mapping_table() -> dict:
    r"""
    Read symbol mapping table from ./data/olocconfig.ini
    :return: Readout table
    """
    return ss.read('symbol_mapping_table', file='./data/olocconfig.ini')


def get_function_conversion_table() -> dict:
    r"""
    Read function conversion table from ./data/olocconfig.ini
    :return: Readout table
    """
    return ss.read('function_conversion_table', file='./data/olocconfig.ini')


def get_function_name_list() -> list:
    r"""
    Get function names in standard function call form (explicit function call)
    :return: Function name list
    """

    function_names = []
    for key, values in get_function_conversion_table().items():
        for func in values:
            if '(' in func and ')' and not '/' in func:  # 只保留标准函数调用形式
                function_names.append(func.split('(')[0])  # 提取函数名

    return list(set(function_names))


def str_fraction_simplifier(fraction: str) -> str:
    r"""
    化简分数
    当分数可化简为整数时,返回整数结果
    :param fraction: 待化简的分数
    :return: 化简后的分数
    """

    def _get_gcd(num1: int, num2: int) -> int:
        r"""
        计算两个整数的最大公约数（使用欧几里得算法）
        :param num1: 整数 1
        :param num2: 整数 2
        :return: 最大公约数
        """
        while num2 != 0:
            num1, num2 = num2, num1 % num2
        return abs(num1)  # 返回正数作为最大公约数

    if "/" not in fraction:
        return fraction

    numerator, denominator = map(int, fraction.split('/'))

    gcd_value = _get_gcd(numerator, denominator)

    numerator //= gcd_value
    denominator //= gcd_value

    if denominator < 0:
        numerator = -numerator
        denominator = -denominator

    return str(numerator) if denominator == 1 else f"{numerator}/{denominator}"

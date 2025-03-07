"""
:author: WaterRun
:date: 2025-03-03
:file: utils.py
:description: Oloc utils
"""

import simpsave as ss


def get_symbol_mapping_table() -> dict:
    r"""
    Read symbol mapping table from ./data/olocdata.ini
    :return: Readout table
    """
    return ss.read('symbol_mapping_table', file='./data/olocdata.ini')


def get_function_conversion_table() -> dict:
    r"""
    Read function conversion table from ./data/olocdata.ini
    :return: Readout table
    """
    return ss.read('function_conversion_table', file='./data/olocdata.ini')


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

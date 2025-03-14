"""
:author: WaterRun
:date: 2025-03-14
:file: oloc_utils.py
:description: Oloc utils
"""

import simpsave as ss

"""
数据读取
"""


def get_symbol_mapping_table() -> dict:
    r"""
    Read symbol mapping table from ./data/olocconfig.ini
    :return: Readout table
    :raise RuntimeError: If table cannot be read or there is an error in the table contents
    """
    try:
        result: dict = ss.read('symbol_mapping_table', file='./data/olocconfig.ini')
    except (KeyError, ValueError, FileNotFoundError):
        raise RuntimeError("olocdata.ini is not accessible or has the wrong format (losing `symbol_mapping_table`). \nVisit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")

    if not (
            all(isinstance(key, str) for key in result.keys()) and
            all(isinstance(value, list) for value in result.values()) and
            all(all(isinstance(item, str) for item in value) for value in result.values())
    ):
        raise RuntimeError("There is a formatting error in the symbol mapping table in olocdata.ini. Visit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")
    return result


def get_function_conversion_table() -> dict:
    r"""
    Read function conversion table from ./data/olocconfig.ini
    :return: Readout table
    :raise RuntimeError: If table cannot be read or there is an error in the table contents
    """
    try:
        result = ss.read('function_conversion_table', file='./data/olocconfig.ini')
    except (KeyError, ValueError, FileNotFoundError):
        raise RuntimeError("olocdata.ini is not accessible or has the wrong format (losing `function_conversion_table`). \nVisit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")
    if not (
            all(isinstance(key, str) for key in result.keys()) and
            all(isinstance(value, list) for value in result.values()) and
            all(all(isinstance(item, str) for item in value) for value in result.values())
    ):
        raise RuntimeError("There is a formatting error in the function conversion table in olocdata.ini. Visit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")
    return result


def get_function_name_list() -> list:
    r"""
    Get function names in standard function call form (explicit function call)
    :return: Function name list
    """

    function_names = []
    for key, values in get_function_conversion_table().items():
        for func in values:
            if '(' in func and ')' and '/' not in func:  # 只保留标准函数调用形式
                function_names.append(func.split('(')[0])  # 提取函数名

    return list(set(function_names))


def get_formatting_output_function_options_table() -> dict:
    r"""
    Read formatting output function options_table from ./data/olocconfig.ini
    :return: Readout table
    :raise RuntimeError: If table cannot be read or there is an error in the table contents
    """
    try:
        result = ss.read('formatting_output_function_options_table', file='./data/olocconfig.ini')
    except (KeyError, ValueError, FileNotFoundError):
        raise RuntimeError("olocdata.ini is not accessible or has the wrong format (losing `formatting_output_function_options_table`). \nVisit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")
    return result


"""test"""
if __name__ == '__main__':
    print(get_formatting_output_function_options_table())

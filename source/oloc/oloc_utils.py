"""
:author: WaterRun
:date: 2025-03-15
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
        raise RuntimeError(
            "olocdata.ini is not accessible or has the wrong format (losing `symbol_mapping_table`). \nVisit "
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
        raise RuntimeError(
            "olocdata.ini is not accessible or has the wrong format (losing `function_conversion_table`). \nVisit "
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
    Read formatting output function options table from ./data/olocconfig.ini
    :return: Readout table
    :raise RuntimeError: If table cannot be read or there is an error in the table contents
    """
    try:
        result = ss.read('formatting_output_function_options_table', file='./data/olocconfig.ini')
    except (KeyError, ValueError, FileNotFoundError):
        raise RuntimeError(
            "olocdata.ini is not accessible or has the wrong format (losing `formatting_output_function_options_table`). \nVisit "
            "https://github.com/Water-Run/oloc for documentation to fix.")

    # 合法性检查
    keys = (
        "space between tokens",
        "number separators add thresholds",
        "number separator interval",
        "underline-style number separator",
        "scientific notation adding thresholds",
        "operator form functions",
        "retain irrational param",
        "non-english character form native irrational",
        "superscript",
    )

    for key in keys:
        if key not in result.keys():
            raise RuntimeError(
                f"The key `{key}` is missing from the formatting output function options table.\nVisit "
                f"https://github.com/Water-Run/oloc for documentation to fix.")

    def _invalidKeyParam(raise_key: str):
        r"""
        封装不合法的键值时的异常抛出
        :param key: 不合法的键
        :return: None
        """
        raise RuntimeError(
            f"The key {raise_key} from the formatting output function options table have parameter error.\nVisit "
            f"https://github.com/Water-Run/oloc for documentation to fix."
        )

    if not (isinstance(result[keys[0]], int) and 0 <= result[keys[0]] <= 10):
        _invalidKeyParam(result[keys[0]])
    if not (isinstance(result[keys[1]], int) and (2 <= result[keys[1]] <= 12 or result[keys[1]] == -1)):
        _invalidKeyParam(result[keys[1]])
    if not (isinstance(result[keys[2]], int) and 1 <= result[keys[2]] <= 6):
        _invalidKeyParam(result[keys[2]])
    if not (isinstance(result[keys[4]], int) and (2 <= result[keys[4]] <= 12 or result[keys[4]] == -1)):
        _invalidKeyParam(result[keys[4]])

    for i in [3, 5, 6, 7, 8]:
        if not isinstance(result[keys[i]], bool):
            _invalidKeyParam(result[keys[i]])

    return result


"""test"""
if __name__ == '__main__':
    print(get_formatting_output_function_options_table())

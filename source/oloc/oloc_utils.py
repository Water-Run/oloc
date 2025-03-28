r"""
:author: WaterRun
:date: 2025-03-29
:file: oloc_utils.py
:description: Oloc utils
"""

import simpsave as ss
from enum import Enum

"""
运算符优先级
"""


def get_operator_priority(operator: str) -> int:
    r"""
    返回运算符的优先级，数字越小优先级越高
    :param operator: 待判断的运算符
    :return: 优先级
    """
    PRIORITY = {
        '+': 5, '-': 5,
        '*': 4, '/': 4,
        '^': 2, '%': 2,
        '!': 3, '|': 3,  # 阶乘、绝对值
        '√': 1,  # 开根号
    }
    return PRIORITY.get(operator, 6)  # 未知符号优先级最低


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


def get_function_mapping_table() -> dict:
    r"""
    Read function mapping table from ./data/olocconfig.ini
    :return: Readout table
    :raise RuntimeError: If table cannot be read or there is an error in the table contents
    """
    try:
        result: dict = ss.read('function_mapping_table', file='./data/olocconfig.ini')
    except (KeyError, ValueError, FileNotFoundError):
        raise RuntimeError(
            "olocdata.ini is not accessible or has the wrong format (losing `function_mapping_table`). \nVisit "
            "https://github.com/Water-Run/oloc for documentation to fix.")

    if not (
            all(isinstance(key, str) for key in result.keys()) and
            all(isinstance(value, list) for value in result.values()) and
            all(all(isinstance(item, str) for item in value) for value in result.values())
    ):
        raise RuntimeError("There is a formatting error in the function mapping table in olocdata.ini. Visit "
                           "https://github.com/Water-Run/oloc for documentation to fix.")
    return result


def get_function_name_list() -> list:
    r"""
    Get function names in standard function call form (explicit function call)
    :return: Function name list
    """

    function_mapping_table = get_function_mapping_table()
    return [alias for aliases in function_mapping_table.values() for alias in aliases]


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
    expected_keys = {
        "function formatting": {
            "operator form functions": bool,
        },
        "readability": {
            "space between tokens": bool,
            "number separators add thresholds": int,
            "number separator interval": int,
            "scientific notation adding thresholds": int,
            "superscript": bool,
            "commonly-used-decimal conversions": bool,
        },
        "custom": {
            "underline-style number separator": bool,
            "retain irrational param": bool,
            "non-ascii character form native irrational": bool,
        },
    }

    # 检查所有顶层键是否存在
    for category in expected_keys:
        if category not in result:
            raise RuntimeError(
                f"The category `{category}` is missing from the formatting output function options table.\nVisit "
                f"https://github.com/Water-Run/oloc for documentation to fix.")

        # 检查每个子键是否存在
        for key, expected_type in expected_keys[category].items():
            if key not in result[category]:
                raise RuntimeError(
                    f"The key `{key}` is missing from the `{category}` category of the formatting output function options table.\nVisit "
                    f"https://github.com/Water-Run/oloc for documentation to fix.")

            # 检查值的类型是否正确
            if not isinstance(result[category][key], expected_type):
                raise RuntimeError(
                    f"The key `{key}` in the `{category}` category has a value of incorrect type. Expected `{expected_type.__name__}`.\nVisit "
                    f"https://github.com/Water-Run/oloc for documentation to fix."
                )

            # 检查数值范围（仅对特定整数字段）
            if category == "readability" and key in ["number separators add thresholds", "number separator interval", "scientific notation adding thresholds"]:
                value = result[category][key]
                if key == "number separators add thresholds" and not (value == -1 or 2 <= value <= 12):
                    raise RuntimeError(
                        f"The key `{key}` in the `{category}` category has an invalid value `{value}`. "
                        f"Expected -1 or an integer between 2 and 12.\nVisit "
                        f"https://github.com/Water-Run/oloc for documentation to fix."
                    )
                elif key == "number separator interval" and not (1 <= value <= 6):
                    raise RuntimeError(
                        f"The key `{key}` in the `{category}` category has an invalid value `{value}`. "
                        f"Expected an integer between 1 and 6.\nVisit "
                        f"https://github.com/Water-Run/oloc for documentation to fix."
                    )
                elif key == "scientific notation adding thresholds" and not (value == -1 or 2 <= value <= 12):
                    raise RuntimeError(
                        f"The key `{key}` in the `{category}` category has an invalid value `{value}`. "
                        f"Expected -1 or an integer between 2 and 12.\nVisit "
                        f"https://github.com/Water-Run/oloc for documentation to fix."
                    )

    return result


"""test"""
if __name__ == '__main__':
    print(get_function_name_list())

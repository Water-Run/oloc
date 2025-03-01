r"""
:author: WaterRun
:date: 2025-02-28
:file: utils.py
:description: Oloc utils
"""

from typing import Dict, List
import simpsave as ss


def get_symbol_mapping_table() -> Dict[str, List[str]]:
    r"""
    Read symbol mapping table from ./data/olocdata.ini
    :return: Readout table
    """
    return ss.read('symbol_mapping_table', file='./data/olocdata.ini')


def get_function_conversion_table() -> Dict[Dict[str, str], List[str]]:
    r"""
    Read function conversion table from ./data/olocdata.ini
    :return: Readout table
    """
    return ss.read('function_conversion_table', file='./data/olocdata.ini')


def get_function_name_list() -> Dict[str]:
    r"""
    Get the names of all functions
    :return: Function name list
    """

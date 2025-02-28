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
    return ss.read('symbol_mapping_table', './data/olocdata.ini')

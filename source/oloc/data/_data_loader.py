r"""
:author: WaterRun
:date: 2025-02-28
:file: _data_loader.py
:description: Script program to generate various table data required for oloc runtime
"""

import simpsave as ss
from typing import Dict, List

r"""
After modification, run this script directly in the "data" path
"""

# Symbol Mapping Table

symbol_mapping_table: Dict[str, List[str]] = {
    "": [" ", "=", "equal", "equals", "is", "rad", "radians", "等于", "等", "是"],
    "^": ["^", "**"],
    "+": ["+", "plus", "加"],
    "-": ["-", "minus", "减"],
    "*": ["*"],
    "/": ["/"],
    "00": [],
    "0": ["0"],
}

# Function Conversion Table

function_conversion_table: dict = {
    {"type": "pow", "result": "pow(x,y)"}: ["pow(x,y)", "x^y"]
}

# Write Data

ss.write('symbol_mapping_table', symbol_mapping_table, 'olocdata.ini')
ss.write('function_conversion_table', function_conversion_table, 'olocdata.ini')

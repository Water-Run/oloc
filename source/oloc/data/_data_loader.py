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
    "": [" ", "=", "equal", "equals", "is", "rad", "radians"],
    "^": ["^", "**"],
    "+": ["+", "plus"],
    "-": ["-", "minus"]
}

# Function Conversion Table

function_conversion_table: dict = {

}

# Write Data

ss.write('symbol_mapping_table', symbol_mapping_table, 'olocdata.ini')
ss.write('function_conversion_table', function_conversion_table, 'olocdata.ini')

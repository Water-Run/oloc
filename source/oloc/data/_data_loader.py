r"""
:author: WaterRun
:date: 2025-03-08
:file: _data_loader.py
:description: Script program to generate various table data required for oloc runtime
"""

import simpsave as ss

r"""
After modification, run this script directly in the "data" path
"""

r"""
Retain decimal places
Type: int
Range: >= 0
Description: The number of decimal places to retain. Must be a positive integer, greater than or equal to zero.
"""
retain_decimal_places: int = 7

r"""
Symbol Mapping Table
Type: dict
Description: This dictionary maps symbols (keys) to a list of possible conversions (values). All strings in the list (except the preserved function names) are converted to the corresponding key. Order: from top to bottom, left to right.
"""
symbol_mapping_table: dict = {
    "": [" ", "=", "_", "equal", "equals", "is", "rad", "radians"],
    "√": ["√", "┌"],
    "°": ["°", "deg", "degree", "^o"],
    "^": ["^", "**"],
    "+": ["+", "plus", "加"],
    "-": ["-", "minus"],
    "*": ["*"],
    "/": ["/"],
    "π": ["π", "p", "pi"]
}

r"""
Function conversion table
Type: dict
Description: This dictionary maps function names (keys) to a list of possible equivalent representations (values). All strings in the list (except the preserved function names) are converted to the corresponding key. Order: from top to bottom, left to right. The standard function name is the function name before the parentheses, and these names will be protected during the symbol mapping phase.
"""
function_conversion_table: dict = {
    "sqrt(x)": ["sqrt(x)", "x^(1/2)", "√x", "pow(x,1/2)"],
    "square(x)": ["square(x)", "x^2", "pow(x,2)", "sq(x)"],
    "cube(x)": ["cube(x)", "x^3", "pow(x,3)", "cub(x)"],
    "reciprocal(x)": ["reciprocal(x)", "x^-1", "pow(x,-1)", "rec(x)"],
    "pow(x,y)": ["pow(x,y)", "x^y", "x**y"],
    "exp(x)": ["exp(x)", "pow(e,x)"],
    "mod(x,y)": ["mod(x,y)", "x%y"],
    "fact(x)": ["fact(x)", "x!"],
    "abs(x)": ["abs(x)", "|x|"],
    "sign(x)": ["sign(x)"],
    "rad(x)": ["rad(x)", "x°"],
    "gcd(x,y)": ["gcd(x,y)"],
    "lcm(x,y)": ["lcm(x,y)"],
}

# Write Data

if ss.write('retain_decimal_places', retain_decimal_places, file='olocdata.ini') and ss.write('symbol_mapping_table', symbol_mapping_table, file='olocdata.ini') and ss.write('function_conversion_table', function_conversion_table, file='olocdata.ini'):
    print('olocdata updated')

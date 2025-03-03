r"""
:author: WaterRun
:date: 2025-03-03
:file: _data_loader.py
:description: Script program to generate various table data required for oloc runtime
"""

import simpsave as ss

r"""
After modification, run this script directly in the "data" path
"""

# Symbol Mapping Table

symbol_mapping_table: dict = {
    "": [" ", "=", "equal", "equals", "is", "rad", "radians"],
    "√": ["√", "┌"],
    "°": ["°", "deg", "degree", "^o"],
    "^": ["^", "**"],
    "+": ["+", "plus"],
    "-": ["-", "minus"],
    "*": ["*"],
    "/": ["/"],
}

# Function Conversion Table

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

if ss.write('symbol_mapping_table', symbol_mapping_table, file='olocdata.ini') and ss.write('function_conversion_table', function_conversion_table, file='olocdata.ini'):
    print('olocdata updated')

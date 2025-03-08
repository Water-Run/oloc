r"""
:author: WaterRun
:date: 2025-03-09
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
    "": [" ", "=", "_", "equal", "equals", "eq", "is", "are", "=>", "->", "rad", "radians", "等", "于", "以", "是", "个"],
    "√": ["√", "┌", "根号"],
    "°": ["°", "deg", "degree", "^o", "度"],
    "^": ["^", "**"],
    "+": ["+", "plus", "add", "加"],
    "-": ["-", "minus", "sub",  "减"],
    "*": ["*", "・", "×", "mul",  "multiply", "乘"],
    "/": ["/", "÷", "div",  "divide", "除"],
    "%": ["%", "余"],
    "!": ["!", "阶层"],
    "π": ["π", "p", "pi", "派", "圆周率"],
    "𝑒": ["𝑒", "e", "自然", "自然底数"],
    ".": [".", "dot", "点"],
    "(": ["(", "（", "左括号", "左小括号"],
    ")": [")", "）", "右括号", "右小括号"],
    "[": ["[", "左中括号"],
    "]": ["]", "右中括号"],
    "{": ["{", "左大括号"],
    "}": ["}", "右大括号"],
    "?": ["?", "def", "dflt", "default", "指定"],
    ",": [","],
    ";": [";"],
    "\\": ["\\"],
    "0": ["0", "zero", "零", "〇"],
    "1": ["1", "one", "一"],
    "2": ["2", "two", "二"],
    "3": ["3", "three", "三"],
    "4": ["4", "four", "四"],
    "5": ["5", "five", "五"],
    "6": ["6", "six", "六"],
    "7": ["7", "seven", "七"],
    "8": ["8", "eight", "八"],
    "9": ["9", "nine", "九"],
    "10": ["10", "ten", "十"],
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
    "pow(x,y)": ["pow(x,y)", "x^y", "x**y", "power(x,y)"],
    "exp(x)": ["exp(x)", "pow(e,x)"],
    "mod(x,y)": ["mod(x,y)", "x%y", "modulo(x,y)"],
    "fact(x)": ["fact(x)", "x!", "factorial(x)"],
    "abs(x)": ["abs(x)", "|x|"],
    "sign(x)": ["sign(x)"],
    "rad(x)": ["rad(x)", "x°"],
    "gcd(x,y)": ["gcd(x,y)"],
    "lcm(x,y)": ["lcm(x,y)"],
}

# Write Data

if ss.write('retain_decimal_places', retain_decimal_places, file='olocdata.ini') and ss.write('symbol_mapping_table', symbol_mapping_table, file='olocdata.ini') and ss.write('function_conversion_table', function_conversion_table, file='olocdata.ini'):
    print('olocdata updated')

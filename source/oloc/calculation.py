r"""
Relevant parts of oloc that perform computational processes
:author: WaterRun
:file: calculation.py
:time: 2025-01-22
"""

symbolic_mapping: dict = {
    r"""
    符号映射表: 表达式中右侧列表中的符号转化为左侧的符号
    """
    
    "+": ["+", "add", "plus"],
    "-": ["-"],
    "*": ["*", "×"],
    "/": ["/", "÷"],
    "(": ["("],
    ")": [")"]
}

preset_function_conversion: dict = {
    r"""
    预设函数转化表: 表达式中右侧列表中的函数表达式转化为左侧函数表达式.其中x,y代表数字
    """
    
    "pow(x,y)": ["pow(x,y)", "x^y"],
    "pow(x,0.5)": ["pow(x,0.5)", "sqrt(x)", "√x"],
    "rdf(x,y)": ["rdf(x,y)", "x.y..."]
}


def preprocessing(expression: str) -> str:

    # 移除空格
    # 移除多余
    # 符号转换
    # 函数转换
    ...

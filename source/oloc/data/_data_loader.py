r"""
:author: WaterRun
:date: 2025-02-28
:file: _data_loader.py
:description: 脚本程序,生成oloc运行中所需的各个表数据
"""

import simpsave as ss

r"""
修改后在data路径下直接运行该脚本
"""

# 符号映射表

symbol_mapping_table: dict = {

}

# 函数转换表

function_conversion_table: dict = {

}

# 写入数据

ss.write('symbol_mapping_table', symbol_mapping_table, 'olocdata.ini')
ss.write('function_conversion_table', function_conversion_table, 'olocdata.ini')

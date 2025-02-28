r"""
:author: WaterRun
:date: 2025-02-28
:file: preprocessor.py
:description: Oloc preprocessor
"""

import simpsave as ss  # 使用simpsave进行数据读取操作
import re

from source.oloc.exceptions import *


class Preprocessor:
    r"""
    预处理器

    :param expression: 待处理的表达式
    """

    expression: str = ''

    def __init__(self, expression: str):
        self.expression = expression

    def _remove_comment(self) -> None:
        r"""
        移除表达式中的@结尾注释和##包裹的自由注释
        :return: None
        """

        # 检查并移除 '@' 之后的注释
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # 查找所有 '#' 的位置
        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        # 如果 '#' 数量不是偶数，说明有不匹配的问题
        if len(hash_positions) % 2 != 0:
            # 找到第一个不匹配的 '#' 的位置
            unmatched_position = hash_positions[-1]
            raise OlocFreeCommentException(
                message="OlocFreeCommentException: Mismatch '#' detected",
                expression=self.expression,
                position=unmatched_position
            )

        # 正则表达式匹配包裹在 ## 中的内容
        pattern = r'#(.*?)#'
        self.expression = re.sub(pattern, '', self.expression).strip()

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()

        symbol_mapping_table = ss.read('symbol_mapping_table', file='data\olocdata.ini') # 读取符号映射表

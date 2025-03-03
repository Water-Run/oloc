r"""
:author: WaterRun
:date: 2025-03-03
:file: preprocessor.py
:description: Oloc preprocessor
"""

import re
import utils

from source.oloc.exceptions import *


class Preprocessor:
    r"""
    预处理器
    实例创建同时进行预处理操作,结果写入self.expression中
    :param expression: 待处理的表达式
    """

    expression: str = ''

    def __init__(self, expression: str):
        self.expression = expression
        self.execute()

    def _remove_comment(self) -> None:
        r"""
        移除表达式中的@结尾注释和##包裹的自由注释
        :return: None
        """

        # 移除结尾注释
        if '@' in self.expression:
            self.expression = self.expression.split('@', 1)[0].strip()

        # 检查自由注释的匹配情况
        hash_positions = [pos for pos, char in enumerate(self.expression) if char == '#']

        if len(hash_positions) % 2 != 0:
            # 获取未匹配的 '#' 的字符位置（基于字符索引）
            unmatched_position = [hash_positions[-1]]  # 单个未匹配的位置放入列表
            raise OlocFreeCommentException(
                exception_type=OlocFreeCommentException.ExceptionType.MISMATCH,  # 枚举类型
                expression=self.expression,  # 错误的表达式
                positions=unmatched_position  # 未匹配的位置列表
            )

        # 移除自由注释 (清除所有 #注释内容# 格式的部分)
        pattern = r'#(.*?)#'
        self.expression = re.sub(pattern, '', self.expression).strip()

    def _symbol_mapper(self):
        r"""
        读取符号映射表,并依次遍历进行映射
        :return: None
        """
        # 符号映射表
        symbol_mapping_table = utils.get_symbol_mapping_table()

        # 遍历映射表并执行替换
        for target, sources in symbol_mapping_table.items():
            for source in sources:
                self.expression = self.expression.replace(source, target)

    def _formal_elimination(self):
        r"""
        消除表达式中的一些特殊形式.包括数字分隔符,括号化简,正负号消除
        :return: None
        """


    def _convert_fraction(self):
        r"""
        将表达式中的各种有理数进行分数化
        :return: None
        """

        def _eliminate_digit_separator(expression: str) -> str:
            r"""
            消除数字分隔符
            :param expression:
            :return:
            """

    def execute(self) -> None:
        r"""
        执行预处理,并将结果写入self.expression中
        :return: None
        """

        self._remove_comment()
        self._symbol_mapper()


"""test"""
while True:
    try:
        print(Preprocessor(input('>>')).expression)
    except OlocException as e:
        print(e)

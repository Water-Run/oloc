r"""
:file: core.py
:author: WaterRun
:time: 2025-02-24
:version: 0.1.0
:description:
"""
from typing import final


@final
class OlocResult:
    r"""
    封装Oloc的结果
    :param result: 结果列表,按照计算顺序正序排布
    """

    def __init__(self, result: list[str]):
        self.result = result

    def __str__(self):
        r"""
        返回结果列表的最后一项.该项及最终结果
        """
        return self.result[-1]


def calculation(expression: str) -> OlocResult:
    ...

r"""
:author: WaterRun
:date: 2025-02-28
:file: core.py
:description: Core of oloc
"""

from result import OlocResult
from exceptions import OlocTimeOutException
import time
from multiprocessing import Process, Queue
from typing import Optional


def _execute_calculation(expression: str, result_queue: Queue):
    """
    实际执行计算的函数。

    :param expression: 要计算的表达式
    :param result_queue: 用于存储计算结果或异常的队列
    """
    try:
        time.sleep(10)  # 模拟长时间计算
        result = OlocResult(expression=expression, result="Calculated Result")
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def calculate(expression: str, *, time_limit: float = 1.0) -> OlocResult:
    """
    计算表达式的结果，并监控计算时间。

    如果计算时间超过 `time_limit` 秒，立即中断并抛出 `OlocTimeOutException`。
    如果 `time_limit` 为负数，则不进行时间监视。

    :param expression: 要计算的表达式
    :param time_limit: 最大允许的计算时间（秒）
    :return: 计算的结果，封装在 OlocResult 中
    :raises OlocTimeOutException: 如果计算时间超过限制
    """
    if time_limit < 0:
        # 不监视时间，直接执行
        result_queue = Queue()
        _execute_calculation(expression, result_queue)
        result = result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    result_queue = Queue()
    process = Process(target=_execute_calculation, args=(expression, result_queue))
    process.start()

    process.join(timeout=time_limit)
    if process.is_alive():
        process.terminate()  # 立即中断子进程
        process.join()
        # 抛出超时异常，标记整个表达式
        raise OlocTimeOutException(
            exception_type=OlocTimeOutException.ExceptionType.TIMEOUT,
            expression=expression,
            positions=list(range(len(expression))),  # 标记整个表达式
            time_limit=time_limit,
            elapsed_time=time_limit,
        )

    # 检查子进程返回的结果
    if not result_queue.empty():
        result = result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    # 如果队列为空，抛出未知异常
    raise RuntimeError("Unexpected error: No result returned from calculation process")


"""test"""
if __name__ == "__main__":
    try:
        # 测试超时
        calculate('123', time_limit=0.1)
    except OlocTimeOutException as e:
        print(e)
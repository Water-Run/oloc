r"""
:author: WaterRun
:date: 2025-03-09
:file: core.py
:description: Core of oloc
"""

from result import OlocResult
from exceptions import *
from multiprocessing import Process, Queue
from preprocessor import Preprocessor


def _execute_calculation(expression: str, result_queue: Queue):
    r"""
    oloc实际执行计算的函数

    :param expression: 要计算的表达式
    :param result_queue: 用于存储计算结果或异常的队列
    """
    """test"""
    try:
        preprocess = Preprocessor(expression)
        preprocess.execute()
        result_queue.put(OlocResult(preprocess.expression, [preprocess.expression]))
    except Exception as e:
        result_queue.put(e)


def calculate(expression: str, *, time_limit: float = -1) -> OlocResult:
    r"""
    计算oloc表达式的结果,并监控计算时间
    如果计算时间超过time_limit秒，立即中断并抛出OlocTimeOutException
    time_limit为负数时不进行时间监视

    :param expression: 要计算的表达式
    :param time_limit: 最大允许的计算时间（秒）
    :return: 计算的结果，封装在 OlocResult 中
    :raises: TypeError: 如果输入的参数类型不正确
    :raises OlocTimeOutException: 如果计算时间超过限制
    """

    # 类型检查
    if not isinstance(expression, str):
        raise TypeError(
            f"oloc's calculate() function: 'expression' must be of type 'str', but got {type(expression).__name__}."
        )

    if isinstance(time_limit, int):
        time_limit = float(time_limit)

    if not isinstance(time_limit, float):
        raise TypeError(
            f"oloc's calculate() function: 'time_limit' must be of type 'float', but got {type(time_limit).__name__}."
        )

    # 存储结果
    result_queue = Queue()

    if time_limit < 0:  # 不监视时间
        _execute_calculation(expression, result_queue)
        if not result_queue.empty():
            result = result_queue.get()
            if isinstance(result, Exception):
                raise result
            return result
    else:
        r"""
        在子进程中调用calculate()执行计算, 一旦超过time_limit则
        """
        process = Process(target=_execute_calculation, args=(expression, result_queue))
        process.start()
        process.join(timeout=time_limit)
        if process.is_alive():
            process.terminate()
            process.join()
            raise OlocTimeOutException(
                exception_type=OlocTimeOutException.ExceptionType.TIMEOUT,
                expression=expression,
                positions=list(range(len(expression))),
                time_limit=time_limit,
                elapsed_time=time_limit,
            )

    if not result_queue.empty():
        result = result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    raise RuntimeError("Unknown exception in calculate() of oloc: result queue is empty")


"""test"""
if __name__ == "__main__":
    while True:
        try:
            user_input = input('>>')
            result = calculate(user_input)
            print("Result:", result.expression)
        except Exception as error:
            print(error)

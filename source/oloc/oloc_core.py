r"""
:author: WaterRun
:date: 2025-03-31
:file: oloc_core.py
:description: Core of oloc
"""
import time

import simpsave as ss
from oloc_result import OlocResult
from oloc_exceptions import *
from multiprocessing import Process, Queue
from oloc_preprocessor import Preprocessor
from oloc_lexer import Lexer
import oloc_utils as utils


def _execute_calculation(expression: str, result_queue: Queue) -> None:
    r"""
    oloc实际执行计算的函数

    :param expression: 要计算的表达式
    :param result_queue: 用于存储计算结果或异常的队列
    """
    """test"""
    try:

        # 预处理
        preprocessor = Preprocessor(expression)
        preprocessor.execute()

        # 词法分析
        lexer = Lexer(preprocessor.expression)
        lexer.execute()

        # 结果封装
        result = OlocResult(lexer.expression, [])
        result_queue.put(OlocResult(result.expression, []))

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
        preprocessor = Preprocessor(expression)
        preprocessor.execute()

        # 词法分析
        lexer = Lexer(preprocessor.expression)
        lexer.execute()

        return OlocResult(lexer.expression, [])
    else:
        r"""
        在子进程中调用calculate()执行计算, 一旦超过time_limit则抛出OlocTimeOutException
        """
        process = Process(target=_execute_calculation, args=(expression, result_queue))
        process.start()
        process.join(timeout=time_limit)
        if process.is_alive():
            process.terminate()
            process.join()
            raise OlocTimeOutException(
                exception_type=OlocTimeOutException.EXCEPTION_TYPE.TIMEOUT,
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


def is_reserved(symbol: str) -> bool:
    r"""
    判断指定符号是否是oloc的保留字。
    注: oloc的保留字不可作为自定义短无理数。

    :param symbol: 被判断的符号
    :return: 如果符号不是保留字，返回 True；否则返回 False
    """
    reserved_keywords = utils.get_function_name_list()
    for value in utils.get_symbol_mapping_table().values():
        reserved_keywords += value

    return any(keyword in symbol for keyword in reserved_keywords)


def run_test(test_file: str, test_key: str, time_limit: float = -1, pause_if_exception: bool = False):
    r"""
    运行测试
    :param test_file: 待测试的simpsave ini文件
    :param test_key: 待测试的simpsave的键
    :param time_limit: 计算限时
    :param pause_if_exception: 在出现异常时是否暂停
    :return: None
    """
    start = time.time()
    try:
        tests = ss.read(test_key, file=test_file)
    except KeyError as k_error:
        print(f'--SimpSave Key Error--\n{k_error}')
    except ValueError as v_error:
        print(f'--SimpSave Value Error--\n{v_error}')
    except FileNotFoundError as f_error:
        print(f'--SimpSave File Not Found Error--\n{f_error}')
    else:
        for test in tests:
            try:
                print(calculate(test, time_limit=time_limit).expression)
            except Exception as error:
                print(error)
                if pause_if_exception:
                    input("continue>>")
        print(f"Finish {len(tests)} cases in {time.time() - start} s")


"""test"""
if __name__ == "__main__":
    run_test("./data/oloctest.ini", "test_cases", -1)

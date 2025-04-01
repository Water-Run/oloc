r"""
:author: WaterRun
:date: 2025-04-01
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
from oloc_parser import Parser
import oloc_utils as utils


def _process_expression(expression: str) -> OlocResult:
    r"""
    处理表达式的核心逻辑，执行预处理、词法分析和语法分析

    :param expression: 要处理的表达式
    :return: 包装在OlocResult中的处理结果
    :raises: 各种oloc异常类型，取决于处理过程中可能出现的错误
    """
    # 预处理
    preprocessor = Preprocessor(expression)
    preprocessor.execute()

    # 词法分析
    lexer = Lexer(preprocessor.expression)
    lexer.execute()

    # 语义分析
    parser = Parser(lexer.tokens)
    parser.execute()

    # 结果封装
    return OlocResult(parser.expression, [])


def _execute_calculation(expression: str, result_queue: Queue) -> None:
    r"""
    在子进程中执行表达式计算的函数

    :param expression: 要计算的表达式
    :param result_queue: 用于存储计算结果或异常的队列
    """
    try:
        result = _process_expression(expression)
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def calculate(expression: str, *, time_limit: float = -1) -> OlocResult:
    r"""
    计算oloc表达式的结果，可选择性地监控计算时间
    如果计算时间超过time_limit秒，立即中断并抛出OlocTimeOutException
    time_limit为负数时不进行时间监视

    :param expression: 要计算的表达式
    :param time_limit: 最大允许的计算时间（秒），负值表示无限制 不推荐启用该功能: 目前版本的Python多线程的原因会带来约0.25s的计算延迟
    :return: 计算的结果，封装在OlocResult中
    :raises TypeError: 如果输入的参数类型不正确
    :raises OlocTimeOutError: 如果计算时间超过限制
    :raises RuntimeError: 如果计算过程中发生未知异常
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

    # 不监视时间的情况下直接执行
    if time_limit < 0:
        return _process_expression(expression)

    # 监视时间的情况下在子进程中执行
    result_queue = Queue()
    process = Process(target=_execute_calculation, args=(expression, result_queue))
    process.start()
    process.join(timeout=time_limit)

    if process.is_alive():
        process.terminate()
        process.join()
        raise OlocTimeOutError(
            exception_type=OlocTimeOutError.TYPE.TIMEOUT,
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
    判断指定符号是否是oloc的保留字
    注: oloc的保留字不可作为自定义短无理数

    :param symbol: 被判断的符号
    :return: 如果符号是保留字，返回True；否则返回False
    """
    reserved_keywords = utils.get_function_name_list()
    for value in utils.get_symbol_mapping_table().values():
        reserved_keywords += value

    return any(keyword in symbol for keyword in reserved_keywords)


def run_test(test_file: str, test_key: str, time_limit: float = -1, pause_if_exception: bool = False) -> None:
    r"""
    运行测试用例集

    :param test_file: 待测试的simpsave ini文件路径
    :param test_key: 待测试的simpsave配置中的键名
    :param time_limit: 计算限时，负值表示无限制
    :param pause_if_exception: 在出现异常时是否暂停程序执行
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
                    input("Press Enter to continue...")
        print(f"Finished {len(tests)} cases in {time.time() - start:.4f} seconds")


"""test"""
if __name__ == "__main__":
    run_test("./data/oloctest.ini", "test_cases", 0.3)
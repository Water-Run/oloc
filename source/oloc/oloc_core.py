r"""
:author: WaterRun
:date: 2025-04-03
:file: oloc_core.py
:description: Core of oloc
"""

import time
import simpsave as ss
from multiprocessing import Process, Queue

import oloc_utils as utils
from oloc_result import OlocResult
from oloc_exceptions import *

from oloc_preprocessor import Preprocessor
from oloc_lexer import Lexer
from oloc_parser import Parser
from oloc_evaluator import Evaluator


def _process_expression(expression: str) -> OlocResult:
    r"""
    Core logic for processing expressions, including preprocessing, lexical analysis, and syntax analysis.

    :param expression: The expression to process.
    :return: The processing result wrapped in an OlocResult object.
    :raises: Various types of oloc exceptions, depending on possible errors during processing.
    """
    # Preprocessing
    preprocessor = Preprocessor(expression)
    preprocessor.execute()

    # Lexical analysis
    lexer = Lexer(preprocessor.expression)
    lexer.execute()

    # Syntax analysis
    parser = Parser(lexer.tokens)
    parser.execute()

    # Evaluation
    evaluator = Evaluator(parser.expression, parser.tokens, parser.ast)
    evaluator.evaluate()

    # Result packaging
    return OlocResult(expression, evaluator.result, preprocessor.time_cost + lexer.time_cost + parser.time_cost + evaluator.time_cost)


def _execute_calculation(expression: str, result_queue: Queue) -> None:
    r"""
    Function to execute expression calculation in a subprocess.

    :param expression: The expression to calculate.
    :param result_queue: A queue to store the calculation result or exceptions.
    """
    try:
        result = _process_expression(expression)
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def calculate(expression: str, *, time_limit: float = -1) -> OlocResult:
    r"""
    Calculate the result of an oloc expression, with optional time monitoring.
    If the calculation time exceeds `time_limit` seconds, it is immediately interrupted, and an OlocTimeOutException is raised.
    If `time_limit` is negative, no time monitoring is performed.
    This feature is not recommended: the current implementation introduces approximately 0.25 seconds of calculation delay.

    :param expression: The expression to calculate.
    :param time_limit: Maximum allowed calculation time (in seconds). A negative value means no time limit.
    :return: The calculation result wrapped in an OlocResult object.
    :raises TypeError: If the input parameter type is incorrect.
    :raises OlocTimeOutError: If the calculation time exceeds the limit.
    :raises RuntimeError: If an unknown error occurs during calculation.
    """

    if not isinstance(expression, str):
        raise TypeError(
            f"oloc.calculate(): 'expression' must be of type 'str', but got {type(expression).__name__}."
        )

    if isinstance(time_limit, int):
        time_limit = float(time_limit)

    if not isinstance(time_limit, float):
        raise TypeError(
            f"oloc.calculate(): 'time_limit' must be of type 'float' | 'int', but got {type(time_limit).__name__}."
        )

    if time_limit < 0:
        return _process_expression(expression)

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

    raise RuntimeError("Unknown exception in oloc.calculate(): result queue is empty\n"
                       "Visit the GitHub page to check out the documentation or submit an issue:\n"
                       "https://github.com/Water-Run/oloc")


def is_reserved(symbol: str) -> bool:
    r"""
    Determine whether the specified symbol is a reserved word in oloc.
    Note: Reserved words in oloc cannot be used as custom short irrational numbers.

    :param symbol: The symbol to check.
    :return: True if the symbol is a reserved word; otherwise, False.
    """
    if symbol.startswith('<--reserved'):
        return True

    reserved_keywords = utils.get_function_name_list()
    for value in utils.get_symbol_mapping_table().values():
        reserved_keywords += value

    return any(keyword in symbol for keyword in reserved_keywords)


def run_test(test_file: str, test_key: str, time_limit: float = -1, pause_if_exception: bool = False) -> None:
    r"""
    Run a test case set.

    :param test_file: Path to the simpsave ini file containing test cases.
    :param test_key: The key in the simpsave configuration to test.
    :param time_limit: Calculation time limit in seconds. A negative value means no limit.
    :param pause_if_exception: Whether to pause execution if an exception occurs.
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

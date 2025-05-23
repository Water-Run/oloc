r"""
:author: WaterRun
:date: 2025-05-22
:file: oloc_cli.py
:description: Oloc CLI - Command Line Interface for oloc library
"""

import os
import sys
import time
from enum import Enum
import traceback

# 只使用__init__暴露的内容
from source.oloc import calculate, is_reserved, run_test, oloc_version


def _parser(command: str, time_limit: float = -1) -> any:
    r"""
    执行指令,并返回结果
    :param command: 待执行的指令
    :param time_limit: 计算超时限制
    :return: 返回的结果: OlocResult或异常
    """
    try:
        result = calculate(command, time_limit=time_limit)
        return result
    except Exception as e:
        return e


def _help():
    r"""
    帮助信息
    :return: None
    """
    print(f"oloc version: {oloc_version()}\n"
          f"BASIC COMMANDS:\n"
          f"  :help     - Display this help information\n"
          f"  :exit     - Exit the program\n"
          f"  :config   - Configure settings (requires parameters)\n"
          f"  :reserved - Check if a symbol is reserved in oloc\n"
          f"  :test     - Run test cases from an ini file\n\n"
          f"CONFIGURATION PARAMETERS:\n"
          f"  -show     - Display current configuration\n"
          f"  -result   - Output only final results (default)\n"
          f"  -steps    - Output step-by-step results\n"
          f"  -detail   - Output detailed calculation information\n"
          f"  -timeout N - Set calculation timeout to N seconds (negative = no timeout)\n\n"
          f"EXTENDED COMMANDS:\n"
          f"  :reserved symbol  - Check if symbol is reserved in oloc\n"
          f"  :test file key    - Run test cases from ini file with specified key\n"
          f"                      Options: --pause (pause on exception)\n"
          f"                               --random N (select N random tests)\n\n"
          f"EXAMPLES:\n"
          f"  >> :config -show          (Shows current configuration)\n"
          f"  >> :config -steps         (Enables step-by-step output)\n"
          f"  >> :config -timeout 5     (Sets calculation timeout to 5 seconds)\n"
          f"  >> :reserved sin          (Checks if 'sin' is a reserved word)\n"
          f"  >> :test tests.ini calc   (Runs tests from tests.ini with key 'calc')\n"
          f"  >> 1+2*3                  (Performs calculation)\n\n"
          f"Any other input will be treated as a calculation expression.\n"
          f"Errors will be displayed with detailed explanations.\n\n"
          f"For complete documentation, visit:\n"
          f"https://github.com/Water-Run/oloc")


def _format_calculation_steps(steps: list) -> str:
    r"""
    格式化计算步骤
    :param steps: 计算步骤列表
    :return: 格式化后的字符串
    """
    if not steps:
        return "No calculation steps available."

    formatted_output = "Calculation steps:\n"
    for i, step in enumerate(steps):
        formatted_output += f"  Step {i+1}: {step}\n"
    return formatted_output


def cli():
    r"""
    CLI程序
    :return: None
    """
    print(f"oloc cli: oloc simple command-line program\n"
          "Type `:help` to get help, and `:exit` to exit the program.")

    class MODES(Enum):
        r"""
        输出模式枚举
        """
        RESULT = 'Result'
        STEPS = 'Steps'
        DETAIL = 'Detail'

    mode = MODES.RESULT
    timeout = -1  # 默认不设置超时

    while True:
        try:
            command = input(">> ")
            command = command.strip()

            if not command:
                continue

            # 处理基本命令
            if command.startswith(":"):
                cmd_parts = command.split(maxsplit=1)
                main_cmd = cmd_parts[0].lower()

                # 退出命令
                if main_cmd == ":exit" or main_cmd == ":quit":
                    break

                # 帮助命令
                elif main_cmd == ":help":
                    _help()

                # 配置命令
                elif main_cmd == ":config":
                    if len(cmd_parts) < 2:
                        print("Error: Missing configuration parameter. Type :help for assistance.")
                        continue

                    config_param = cmd_parts[1].strip()

                    if config_param == '-result':
                        mode = MODES.RESULT
                        print(f'Set mode: {mode.value}')

                    elif config_param == '-steps':
                        mode = MODES.STEPS
                        print(f'Set mode: {mode.value}')

                    elif config_param == '-detail':
                        mode = MODES.DETAIL
                        print(f'Set mode: {mode.value}')

                    elif config_param == '-show':
                        print(f'Config Info:\n'
                              f'  Mode: {mode.value}\n'
                              f'  Timeout: {timeout if timeout >= 0 else "Disabled"} seconds')

                    elif config_param.startswith('-timeout '):
                        try:
                            timeout_value = float(config_param[9:].strip())
                            timeout = timeout_value
                            print(f'Set timeout: {timeout if timeout >= 0 else "Disabled"} seconds')
                        except ValueError:
                            print("Error: Invalid timeout value. Please provide a valid number.")

                    else:
                        print('Invalid Config. Type :help for assistance.')

                # 检查保留字命令
                elif main_cmd == ":reserved":
                    if len(cmd_parts) < 2:
                        print("Error: Missing symbol to check. Usage: :reserved symbol")
                    else:
                        symbol = cmd_parts[1].strip()
                        if is_reserved(symbol):
                            print(f"'{symbol}' is a reserved word in oloc.")
                        else:
                            print(f"'{symbol}' is not reserved and can be used as a custom irrational.")

                # 运行测试命令
                elif main_cmd == ":test":
                    if len(cmd_parts) < 2:
                        print("Error: Missing parameters. Usage: :test file key [options]")
                    else:
                        test_args = cmd_parts[1].split()
                        if len(test_args) < 2:
                            print("Error: Both file and key parameters are required for testing.")
                        else:
                            test_file = test_args[0]
                            test_key = test_args[1]

                            # 解析其他选项
                            pause_if_exception = "--pause" in test_args

                            random_choice = -1  # 默认不随机选择
                            for i, arg in enumerate(test_args):
                                if arg == "--random" and i+1 < len(test_args):
                                    try:
                                        random_choice = int(test_args[i+1])
                                    except ValueError:
                                        pass

                            print(f"Running tests from file '{test_file}' with key '{test_key}'")
                            print(f"Options: {'pause on exception, ' if pause_if_exception else ''}{'random selection: ' + str(random_choice) if random_choice > 0 else 'all tests'}")

                            try:
                                if not os.path.exists(test_file):
                                    print(f"Error: Test file '{test_file}' not found.")
                                else:
                                    run_test(
                                        test_file=test_file,
                                        test_key=test_key,
                                        time_limit=timeout,
                                        pause_if_exception=pause_if_exception,
                                        random_choice=random_choice
                                    )
                            except Exception as e:
                                print(f"Error running tests: {str(e)}")

                # 未知命令
                else:
                    print(f"Unknown command: {main_cmd}. Type :help for assistance.")

            # 处理计算表达式
            else:
                start_time = time.time()
                result = _parser(command, time_limit=timeout)
                elapsed_time = time.time() - start_time

                if isinstance(result, Exception):
                    print(f"{result}")
                else:
                    # 根据模式显示结果
                    if mode == MODES.RESULT:
                        # 只显示最终结果
                        print(f"Result: {result}")

                    elif mode == MODES.STEPS:
                        # 显示计算步骤和最终结果
                        print(_format_calculation_steps(result.result))
                        print(f"Result: {result}")

                    elif mode == MODES.DETAIL:
                        # 显示详细信息
                        print(f"Original expression: {result.expression}")
                        print(_format_calculation_steps(result.result))
                        print(f"Result: {result}")
                        print(f"Calculation time: {result.time_cost:.6f} ms")

                        # 尝试转换为各种类型并显示
                        try:
                            float_value = float(result)
                            print(f"As float: {float_value}")
                        except Exception as e:
                            print(f"Cannot convert to float: {str(e)}")

                        try:
                            int_value = int(result)
                            print(f"As integer: {int_value}")
                        except Exception as e:
                            print(f"Cannot convert to integer: {str(e)}")

                        try:
                            from fractions import Fraction
                            frac_value = result.get_fractions()
                            print(f"As fraction: {frac_value}")
                        except Exception as e:
                            print(f"Cannot convert to fraction: {str(e)}")

                    # 显示计算耗时
                    print(f"Time: {elapsed_time:.6f} seconds")

        except KeyboardInterrupt:
            print("\nOperation interrupted. Type :exit to quit.")
            continue

        except EOFError:
            print("\nEnd of input. Exiting program.")
            break

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            traceback.print_exc()

    print('GitHub: https://github.com/Water-Run/oloc')


if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

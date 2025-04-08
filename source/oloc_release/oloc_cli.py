r"""
:author: WaterRun
:date: 2025-04-09
:file: oloc_cli.py
:description: Oloc CLI
"""

from enum import Enum


def _parser(command: str) -> any:
    r"""
    执行指令,并返回结果
    :param command: 待执行的指令
    :return: 返回的结果: OlocResult或异常
    """


def _help():
    r"""
    帮助信息
    :return: None
    """
    print(f"oloc version: 0.1.0\n"
          f"BASIC COMMANDS:\n"
          f"  :help     - Display this help information\n"
          f"  :exit     - Exit the program\n"
          f"  :config   - Configure settings (requires parameters)\n\n"
          f"CONFIGURATION PARAMETERS:\n"
          f"  -show     - Display current configuration\n"
          f"  -result   - Output only final results (default)\n"
          f"  -steps    - Output step-by-step results\n"
          f"  -detail   - Output detailed calculation information\n\n"
          f"EXAMPLES:\n"
          f"  >> :config -show     (Shows current configuration)\n"
          f"  >> :config -steps    (Enables step-by-step output)\n"
          f"  >> 1+2*3             (Performs calculation)\n\n"
          f"Any other input will be treated as a calculation expression.\n"
          f"Errors will be displayed with detailed explanations.\n\n"
          f"For complete documentation, visit:\n"
          f"https://github.com/Water-Run/oloc")


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

    while True:
        command = input(">>")
        if command.strip() == "":
            continue
        elif command.startswith(":exit"):
            break
        elif command.startswith(":help"):
            _help()
        elif command.startswith(":config"):
            match command[7:].strip():
                case '-result':
                    mode = MODES.RESULT
                    print(f'set mode: {mode}')
                case '-steps':
                    mode = MODES.STEPS
                    print(f'set mode: {mode}')
                case '-detail':
                    mode = MODES.DETAIL
                    print(f'set mode: {mode}')
                case '-show':
                    print(f'Config Info: \n'
                          f'mode: {mode}')
                case _:
                    print('Invalid Config')
        else:
            result = _parser(command)
            if isinstance(result, Exception):
                print(result)
            else:
                match mode:
                    case MODES.RESULT:
                        ...
                    case MODES.STEPS:
                        ...
                    case MODES.DETAIL:
                        ...

    print('GitHub: https://github.com/Water-Run/oloc')


if __name__ == '__main__':
    cli()

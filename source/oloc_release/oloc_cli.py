r"""
:author: WaterRun
:date: 2025-04-08
:file: oloc_cli.py
:description: Oloc CLI
"""

from enum import Enum


def _parser(command: str) -> any:
    r"""
    执行指令,并返回结果
    :param command: 待执行的指令
    :return: 返回的结果:OlocResult或异常
    """


def _help():
    r"""
    帮助信息
    :return: None
    """


def cli():
    r"""
    CLI程序
    :return: None
    """
    print(f"oloc cli: oloc simple command-line program\n"
          f"version: 0.1.0\n"
          "Type `:help` to get help, and `:exit` to exit the program.\n"
          "`>>` indicates waiting for an input expression.")

    invalid_count = 0

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
                case '-r':
                    mode = MODES.RESULT
                    print(f'set mode: {mode}')
                case '-s':
                    mode = MODES.STEPS
                    print(f'set mode: {mode}')
                case '-d':
                    mode = MODES.DETAIL
                    print(f'set mode: {mode}')
                case '-show':
                    print(f'Config Info: \n'
                          f'mode: {mode}')
        else:
            if not _parser(command):
                invalid_count += 1
                if invalid_count > 3:
                    print('You seem to have entered an unparsable expression several times. Try reading the tutorial '
                          'documentation for help:\n'
                          'https://github.com/Water-Run/oloc')
                else:
                    print('Invalid Command')

    print('GitHub: https://github.com/Water-Run/oloc')


if __name__ == '__main__':
    cli()

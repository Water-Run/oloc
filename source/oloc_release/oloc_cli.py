r"""
:author: WaterRun
:date: 2025-04-04
:file: oloc_cli.py
:description: Oloc CLI
"""


from ..oloc import oloc_core as oloc


class _Config:
    r"""
    CLI配置
    """

    show_steps = False
    show_time_cost = False
    show_error_detail = False

    @staticmethod
    def reset():
        r"""
        重置配置
        :return: None
        """
        _Config.show_steps = False
        _Config.show_time_cost = False
        _Config.show_error_detail = False

    @staticmethod
    def console():
        r"""
        配置子终端
        :return: None
        """
        print("oloc cli config console: \n"
              "")

    def __repr__(self):
        return (f"oloc cli config: \n"
                f"show steps: {_Config.show_steps}\n"
                f"show time cost: {_Config.show_time_cost}\n"
                f"show error detail: {_Config.show_error_detail}")

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a static class and cannot be instantiated.")


def _parser(command: str) -> bool:
    r"""
    执行指令,并输出结果
    :param command: 待执行的指令
    :return: 指令是否成功解析
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
    print(f"oloc CLI: oloc simple command-line program\n"
          "Type `:help` to get help, and `:exit` to exit the program.\n"
          "`>>` indicates waiting for an input expression.")

    invalid_count = 0

    while True:
        command = input(">>")
        if command.strip() == "":
            continue
        elif command.startswith(":exit"):
            break
        elif command.startswith(":help"):
            _help()
        elif command.startswith(":config"):
            _Config.console()
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

from .core import ConsoleAccount

import argparse
import traceback

from rich.console import Console
from rich.panel import Panel


def main():
    app = ConsoleAccount()

    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=100)
    )

    parser.add_argument('-d', '--default-settings',
                        dest='default_settings',
                        action='store_true',
                        help='Включить настройки по умолчанию')

    parser.add_argument('--skip-auth',
                        dest='skip_auth',
                        action='store_true',
                        help='Пропустить авторизацию [ сетевые функции не будут работать ]')

    args = parser.parse_args()

    try:
        app.run(default_settings=args.default_settings, auth=not args.skip_auth)
    except Exception as e:
        app.create_log('MAIN_LOGGER', str(e))
        console = Console()
        console.print(Panel(f'{e}\n\n'
                            f'{"-" * (console.width - 4)}'
                            f'\n\n{traceback.format_exc()}\n\n'
                            f'ПРЕКРАЩЕНА РАБОТА ПРОГРАММЫ',
                            style='bold red',
                            title='[bold red]## ОШИБКА ##'))
        app.exit_app()


if __name__ == '__main__':
    main()

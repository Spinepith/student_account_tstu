from importlib.metadata import distributions
import os
import sys
import time
import threading
import subprocess

import datetime
import traceback


def logger(logger_name: str, error: Exception):
    time_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    with open(f'../logs/{time_now}_ERROR.txt', 'w') as log:
        log.write(f'{time_now} - {logger_name} -> ERROR: {str(error)}\n\n{traceback.format_exc()}')
    raise error


def main():
    try:
        with open("../requirements.txt", "r") as file:
            reqs = [req.strip('\n') for req in file.readlines()]

        installed = []
        if os.path.exists('../libs'):
            installed = [f'{i.name}=={i.version}' for i in distributions(path=['../libs'])]

        not_installed = []
        for req in reqs:
            if req not in installed:
                not_installed.append(req)

        def timer_thread(start_time, stop):
            while not stop.is_set():
                total_seconds = time.time() - start_time
                seconds = total_seconds % 60
                minutes = total_seconds // 60

                elapsed = (f'Прошло: '
                           f'{"0" + str(int(minutes))}:'
                           f'{str(seconds)[:2] if seconds >= 10 else "0" + str(seconds)[:1]}')
                print(f'\033[6;1H\033[35m{" " * ((width - len(elapsed)) // 2)}{elapsed}\033[0m', end='\r')

        if not_installed:
            os.system('cls' if os.name == 'nt' else 'clear')

            text = 'Загрузка зависимостей'
            print(' ' * ((os.get_terminal_size().columns - len(text)) // 2) + f'\033[35m{text}\033[0m\n')

            stop_timer = threading.Event()
            timer = threading.Thread(target=timer_thread, args=(time.time(), stop_timer))
            timer_start = False

            try:
                current_complete = 0
                for iteration in range(len(not_installed)):
                    width = os.get_terminal_size().columns - 2

                    if iteration == 0:
                        complete = 0
                    else:
                        complete = (width * iteration) // len(not_installed)

                    package_name_parts = not_installed[iteration].partition('==')
                    package = f'{package_name_parts[0]} version {package_name_parts[2]}'

                    if iteration == 0:
                        print(f'\033[3;1H\033[33m{" " * ((width - len(package)) // 2)}{package}\033[0m')
                        print(f'\033[4;1H\033[32m|{"░" * width}|\033[0m')
                    else:
                        print(f'\033[3;1H\033[33m{" " * ((width - len(package)) // 2)}{package}\033[0m')
                        for i in range(current_complete, complete + 1):
                            print(f'\033[4;1H\033[32m|{"█" * i}{"░" * (width - i)}|\033[0m', end='\r')
                            time.sleep(.01)

                    current_complete = complete

                    if not timer_start:
                        timer_start = True
                        timer.start()

                    try:
                        subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', not_installed[iteration], '--target=../libs'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            check=True,
                            text=True
                        )
                    except subprocess.CalledProcessError as e:
                        logger('INSTALL_REQUIREMENTS_LOGGER', e)

                # ЗАПОЛНЕНИЕ ПОСЛЕДНЕЙ ИТЕРАЦИИ ПРОГРЕСС БАРА
                width = os.get_terminal_size().columns - 2
                for i in range(current_complete, width + 1):
                    print(f'\033[4;1H\033[32m|{"█" * i}{"░" * (width - i)}|\033[0m', end='\r')
                    time.sleep(.01)
            except KeyboardInterrupt:
                pass
            finally:
                stop_timer.set()
                timer.join()
    except Exception as e:
        logger('INSTALL_REQUIREMENTS_LOGGER', e)


if __name__ == "__main__":
    main()

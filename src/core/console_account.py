from .web_account import WebAccount
from src.settings import ConsoleAppSettings
from src.settings import SettingsMenu
from src.utils import JSONManager

import os
import sys
import logging
import datetime
import random

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode

from art import text2art
import questionary

from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import HEAVY


class ConsoleAccount(ConsoleAppSettings):
    __account: WebAccount
    __console: Console
    __settings_object: ConsoleAppSettings
    __settings_menu: SettingsMenu
    __json_manager: JSONManager

    def __init__(self, default_settings=False):
        super().__init__(default_settings)

        self.__console = Console()
        self.__settings_object = ConsoleAppSettings(default_settings)
        self.__settings_menu = SettingsMenu(self.__console, self.__settings_object, self.exit_app)
        self.__json_manager = JSONManager(directory='data', create=True)

    def __login(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if not self.__json_manager.find_file('user_data.json'):
            self.__warning_panel(
                Text('Если ввели неверный логин и перешли к паролю, напишите "назад" или "back"', justify='center'),
                end='\n'
            )

            auth_style = questionary.Style(self.__settings_object._settings['selection_menu'])

            input_login = [
                {
                    'type': 'text',
                    'name': 'login',
                    'message': 'Введите логин:',
                    'qmark': '*',
                    'style': auth_style
                }
            ]

            input_password = [
                {
                    'type': 'password',
                    'name': 'password',
                    'message': 'Введите пароль:',
                    'qmark': '*',
                    'style': auth_style
                }
            ]

            # ВВОД ДАННЫХ ДЛЯ АВТОРИЗАЦИИ
            bad_symbols = '`~!@#$%^&*()-+={}[]:;"\'<>,.?/|\\'
            try:
                login = questionary.unsafe_prompt(
                    input_login, true_color=self.__settings_object._settings['true_color']
                )['login']
                while not login or any(i in bad_symbols for i in login) or len(login) < 4:
                    self.__console.print(f'[bold {self.__settings_object._settings["error"]}]'
                                         f'# Логин введен неправильно\n')
                    login = questionary.unsafe_prompt(
                        input_login, true_color=self.__settings_object._settings['true_color']
                    )['login']

                password = questionary.unsafe_prompt(
                    input_password, true_color=self.__settings_object._settings['true_color']
                )['password']
                if password.upper() in ('НАЗАД', 'BACK'):
                    return False

                while not password or len(password) < 4:
                    self.__console.print(f'[bold {self.__settings_object._settings["error"]}]'
                                         f'# Пароль введен неправильно\n')
                    password = questionary.unsafe_prompt(
                        input_password, true_color=self.__settings_object._settings['true_color']
                    )['password']

                    if password.upper() in ('НАЗАД', 'BACK'):
                        return False
            except KeyboardInterrupt:
                return self.exit_app()
        else:
            user_data = self.__json_manager.get_data('user_data.json')
            try:
                if not ('login' or 'password') in user_data:
                    self.__json_manager.remove_file('user_data.json')
                    return False
            except TypeError:
                self.__json_manager.remove_file('user_data.json')
                return False

            login, password = user_data['login'], self.__crypto_password(user_data['password'])

            input_color = next(
                value for key, value in self.__settings_object._settings["selection_menu"] if key == 'answer'
            )
            self.__console.print(f'\n[{self.__settings_object._settings["input"]}]* Введите логин: '
                                 f'[{input_color}]{login}')
            if self.__settings_object._settings['password_style'] != 'encrypted':
                self.__console.print(f'[{self.__settings_object._settings["input"]}]* Введите пароль: '
                                     f'[{input_color}]{self.__settings_object._settings["password_style"] * 10}')
            else:
                encrypted_password = list(user_data['password'])
                random.shuffle(encrypted_password)
                encrypted_password = ''.join(encrypted_password)
                self.__console.print(f'[{self.__settings_object._settings["input"]}]* Введите пароль: '
                                     f'[{input_color}]{encrypted_password}')

        self.__warning_panel(
            'Дождитесь завершения авторизации...\n'
            'Первый запуск может занять чуть больше времени\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК',
            start='\n', end=''
        )

        # УБИРАЕТ ПОВТОРНЫЙ ЗАПУСК БРАУЗЕРА | БРАУЗЕР ЕСЛИ ЕСТЬ ОБЪЕКТ АККАУНТА (ПРИ ЕГО СОЗДАНИИ ЗАПУСКАЕТСЯ БРАУЗЕР) |
        if not hasattr(self, '_ConsoleAccount__account'):
            self.__account = WebAccount()

        auth = self.__account.enter_login(login, password)

        if auth[0]:
            self.__console.print('АВТОРИЗАЦИЯ ПРОШЛА УСПЕШНО',
                                 style=f'bold {self.__settings_object._settings["input"]}')

            password = self.__crypto_password(password, encrypt=True)

            user_data = {
                'name': auth[1],
                'login': login,
                'password': password
            }
            self.__json_manager.write_data('user_data.json', user_data)
            return True
        else:
            self.__error_panel(f'{auth[1]}')
            self.__json_manager.remove_file('user_data.json')

            self.__console.print(Rule())

            choice_style = questionary.Style(self.__settings_object._settings['selection_menu'])

            try:
                choice = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'select',
                            'name': 'try_again',
                            'qmark': '*',
                            'message': 'Попробовать еще раз?',
                            'choices': ['Попробовать', 'Закрыть программу'],
                            'style': choice_style,
                            'pointer': self.__settings_object._settings['menu_pointer_style']
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )
                return False if choice['try_again'] == 'Попробовать' else self.exit_app()
            except KeyboardInterrupt:
                return self.exit_app()

    def __menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if self.__settings_object._settings['welcome_message'] == 'true':
            user_name = self.__json_manager.get_data('user_data.json')['name']
            self.__console.print(
                Panel(
                    Text(f'Добро пожаловать в личный кабинет студента, {user_name}!', justify='center'),
                    style=self.__settings_object._settings['user_name_box_color'],
                    box=self.__settings_object._settings['welcome_box_style'],
                    safe_box=True
                )
            )

        if os.name != 'nt' and self.__settings_object._settings['warning_about_exit'] == 'true':
            self.__console.print(
                Panel(
                    Text(
                        'Не закрывайте программу через крестик или command + Q\n'
                        '[ это сообщение можно отключить в дополнительных настройках ]',
                        justify='center'
                    ),
                    style=self.__settings_object._settings['warning'],
                    box=self.__settings_object._settings['messages_box_style'],
                    safe_box=True
                )
            )

        menu_choices = [
            'Мои личные данные',
            'Мои баллы по всем предметам',
            'Баллы по конкретному предмету',
            'Зачетная книжка',
            'Расписание',
            'Мой рейтинг',
            'Показать логин и пароль',
            'Настройки',
            'Выйти из личного кабинета',
            'Закрыть программу'
        ]

        menu_style = questionary.Style(self.__settings_object._settings['selection_menu'])
        try:
            main_menu = questionary.unsafe_prompt(
                [
                    {
                        'type': 'select',
                        'name': 'main_menu',
                        'qmark': '*',
                        'message': 'Что вас интересует?',
                        'choices': menu_choices,
                        'style': menu_style,
                        'pointer': self.__settings_object._settings['menu_pointer_style']
                    }
                ],
                true_color=self.__settings_object._settings['true_color']
            )['main_menu']

            match main_menu:
                case 'Мои личные данные':
                    self.__get_personal_data()
                case 'Мои баллы по всем предметам':
                    self.__get_check_marks(all_lessons=True)
                case 'Баллы по конкретному предмету':
                    self.__get_check_marks()
                case 'Зачетная книжка':
                    self.__get_report_card()
                case 'Расписание':
                    self.__get_schedule()
                case 'Мой рейтинг':
                    self.__get_my_rating()
                case 'Показать логин и пароль':
                    self.__show_login_password()
                case 'Настройки':
                    self.__settings()
                case 'Выйти из личного кабинета':
                    self.__logout()
                case 'Закрыть программу':
                    self.exit_app()
        except KeyboardInterrupt:
            return self.exit_app()

    def __back(self):
        back_style = questionary.Style(self.__settings_object._settings['selection_menu'])

        try:
            questionary.unsafe_prompt(
                [
                    {
                        'type': 'select',
                        'name': 'back',
                        'qmark': '',
                        'message': '',
                        'choices': [f'НАЗАД {"#" * (self.__console.width - 6)}'],
                        'style': back_style,
                        'pointer': self.__settings_object._settings['menu_pointer_style']
                    }
                ],
                true_color=self.__settings_object._settings['true_color']
            )
            self.__menu()
        except KeyboardInterrupt:
            self.exit_app()

    def run(self, default_settings=False, auth=True):
        try:
            if default_settings:
                self.__init__(default_settings=True)

            if auth:
                while not self.__login():
                    pass

            self.__menu()
        except Exception as e:
            self.__error_panel(str(e), important=True)

            self.create_log('RUN_LOGGER', str(e))

            self.__console.print(Rule())
            style = questionary.Style(self.__settings_object._settings['selection_menu'])
            try:
                restart = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'select',
                            'name': 'restart',
                            'qmark': '*',
                            'message': 'Перезапустить с дефолтными настройками? [ ваши настройки не потеряются ]',
                            'choices': ['Перезапустить', 'Закрыть программу'],
                            'style': style,
                            'pointer': '-'
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )['restart']

                if restart != 'Перезапустить':
                    return self.exit_app()

                try:
                    if hasattr(self, f'_{self.__class__.__name__}__account'):
                        self.__account.quit()
                        delattr(self, f'_{self.__class__.__name__}__account')
                    self.run(default_settings=True)
                except Exception as e:
                    self.__error_panel(e, important=True)
                    self.create_log('RUN_LOGGER', str(e))
                    return self.exit_app()
            except KeyboardInterrupt:
                return self.exit_app()

    def exit_app(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            self.__logotype()
        except AttributeError:
            pass

        if self.__json_manager.find_file('user_data.json'):
            try:
                if self.__settings_object._settings['welcome_message'] == 'true':
                    user_name = self.__json_manager.get_data('user_data.json')['name']
                    self.__console.print(
                        Panel(
                            Text(f'До встречи, {user_name.split()[1]}!', justify='center'),
                            style=self.__settings_object._settings['user_name_box_color'],
                            box=self.__settings_object._settings['welcome_box_style'],
                            safe_box=True
                        )
                    )
            except AttributeError:
                pass

        self.__console.print('-> ПРОГРАММА ЗАКРОЕТСЯ САМА <-', style='#8c8eff', justify='center')

        if hasattr(self, f'_{self.__class__.__name__}__account'):
            self.__account.quit()
        sys.exit(0)

    """ ФУНКЦИИ, ВЫДАЮЩИЕ ИНФОРМАЦИЮ, КОТОРАЯ ИНТЕРЕСУЕТ ПОЛЬЗОВАТЕЛЯ """
    def __get_personal_data(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        self.__warning_panel(
            'Дождитесь завершения операции...\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
        )

        personal_data = self.__account.personal_data()

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if personal_data:
            personal_table = self.__make_table(personal_data['Личные данные'])
            financing_table = self.__make_table(personal_data['Финансирование'])
            orders_table = self.__make_table(personal_data['Приказы'])

            self.__console.print(personal_table)
            self.__console.print(financing_table, '\n')
            self.__console.print(orders_table)
        else:
            self.__error_panel(personal_data[1])

        self.__back()

    def __get_check_marks(self, all_lessons=False):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if all_lessons:
            self.__warning_panel(
                'Дождитесь завершения операции...\n'
                'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
            )
            marks, marks_details = self.__account.check_marks(details=True)
        else:
            lessons = self.__account.get_lessons()
            if not lessons:
                self.__warning_panel(
                    'Чтобы вернуться в меню, напишите "назад"\n'
                    'Чтобы получить список дисциплин, напиши "дисциплины"'
                )

                input_lesson_style = questionary.Style(self.__settings_object._settings['selection_menu'])
                try:
                    lesson = questionary.unsafe_prompt(
                        [
                            {
                                'type': 'text',
                                'name': 'input_lesson',
                                'qmark': '*',
                                'message': 'Введите название дисциплины [ можно не полностью ]:',
                                'style': input_lesson_style
                            }
                        ],
                        true_color=self.__settings_object._settings['true_color']
                    )['input_lesson']
                except KeyboardInterrupt:
                    return self.exit_app()
            else:
                try:
                    select_lesson_style = questionary.Style(self.__settings_object._settings['selection_menu'])
                    lesson = questionary.unsafe_prompt(
                        [
                            {
                                'type': 'select',
                                'name': 'select_lesson',
                                'qmark': '*',
                                'message': 'Выберите дисциплину:',
                                'choices': list(
                                    [lesson for journal in lessons.values() for lesson in journal] + ['НАЗАД']),
                                'style': select_lesson_style,
                                'pointer': self.__settings_object._settings['menu_pointer_style']
                            }
                        ],
                        true_color=self.__settings_object._settings['true_color']
                    )['select_lesson']
                except KeyboardInterrupt:
                    return self.exit_app()

            if lesson.upper() == 'НАЗАД' or lesson.upper() == 'BACK':
                self.__menu()

            if lesson.upper() == 'ДИСЦИПЛИНЫ' or lesson.upper() == 'LESSONS':
                os.system('cls' if os.name == 'nt' else 'clear')
                self.__logotype()
                self.__warning_panel(
                    'Дождитесь завершения операции...\n'
                    'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
                )
                self.__account.get_lessons(search=True)
                return self.__get_check_marks()

            self.__warning_panel(
                'Дождитесь завершения операции...\n'
                'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК',
                start='\n'
            )
            marks, marks_details = self.__account.check_marks(lesson, details=True)

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if marks and marks_details:
            user_name = self.__json_manager.get_data('user_data.json')['name']
            user_name = next((name for name in marks.keys() if name == user_name), None)

            if user_name:
                user_name_index = list(i for i in marks.keys()).index(user_name)
                selected_color = f'[{self.__settings_object._settings["me_in_table_color"]}]'

                if not all_lessons:
                    marks = dict(list(marks.items())[:user_name_index] +
                                 [(selected_color + user_name, [selected_color + i for i in marks[user_name]])] +
                                 list(marks.items())[user_name_index + 1:])

                    marks_details = dict(list(marks_details.items())[:user_name_index] +
                                         [(selected_color + user_name,
                                           [selected_color + i for i in marks_details[user_name]])] +
                                         list(marks_details.items())[user_name_index + 1:])

            marks = list([name] + data for name, data in marks.items())
            marks_details = list([name] + data for name, data in marks_details.items())

            if not all_lessons:
                self.__console.print(self.__make_table(marks_details, marks[0][0]), '\n')
                self.__console.print(self.__make_table(marks, 'Краткая информация'))
            else:
                for table in marks_details:
                    self.__console.print(self.__make_table(table[1:], table[0]), '\n')
                self.__console.print(self.__make_table(marks, 'Краткая информация'))
        else:
            self.__error_panel(marks[1])

        self.__back()

    def __get_report_card(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        self.__warning_panel(
            'Дождитесь завершения операции...\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
        )

        report_card = self.__account.report_card()

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if report_card:
            additional = self.__make_table(report_card['Дополнительные данные'])
            self.__console.print(additional, '\n')

            for index, (key, value) in enumerate(list(report_card.items())[1:], start=1):
                if value[0]:
                    table = self.__make_table(value[0], key)
                    self.__console.print(table, '\n')
                if value[1]:
                    table = self.__make_table(value[1], key)
                    self.__console.print(table, '\n')

                if index + 1 < len(report_card):
                    if list(report_card.values())[index + 1] != [[], []]:
                        self.__console.print(
                            f'[{self.__settings_object._settings["split_table_line_color"]}]'
                            f'{self.__settings_object._settings["split_table_symbol_style"]}' *
                            self.__console.width, '\n\n'
                        )
        else:
            self.__error_panel(report_card[1])

        self.__back()

    def __get_schedule(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        self.__warning_panel(
            'Дождитесь завершения операции...\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
        )

        schedule = self.__account.schedule()

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if schedule:
            weeks = list(i for i in schedule.keys())

            schedule_table1 = self.__make_table(schedule[weeks[1]], weeks[1])
            schedule_table2 = self.__make_table(schedule[weeks[2]], weeks[2])

            self.__inf_panel(schedule[weeks[0]], center=True)
            self.__console.print('\n', schedule_table1, '\n')
            self.__console.print(schedule_table2)
        else:
            self.__error_panel(schedule[1])

        self.__back()

    def __get_my_rating(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        groups = self.__account.get_groups('check')
        if not groups:
            self.__warning_panel(
                'Узнаю в каких группах вы есть...\n'
                'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
            )
            groups = self.__account.get_groups('get')

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        style = questionary.Style(self.__settings_object._settings['selection_menu'])
        try:
            selected_group = questionary.unsafe_prompt(
                [
                    {
                        'type': 'select',
                        'name': 'select_group',
                        'qmark': '*',
                        'message': 'Выберите группу:',
                        'choices': list(groups) + ['НАЗАД'],
                        'style': style,
                        'pointer': self.__settings_object._settings['menu_pointer_style']
                    }
                ],
                true_color=self.__settings_object._settings['true_color']
            )['select_group']
        except KeyboardInterrupt:
            return self.exit_app()

        if selected_group == 'НАЗАД':
            self.__menu()

        self.__warning_panel(
            'Дождитесь завершения операции...\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК',
            start='\n'
        )
        rating = self.__account.my_rating(selected_group)

        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        if rating:
            user_name = self.__json_manager.get_data('user_data.json')['name']
            selected_color = f'[{self.__settings_object._settings["me_in_table_color"]}]'

            for key, value in rating.items():
                if not next((i for i in value if 'Данных не найдено' in i), None):
                    user_name_index = next(index for index, position in enumerate(value) if user_name in position)
                    value = (value[:user_name_index] +
                             [list(selected_color + i for i in value[user_name_index])] +
                             value[user_name_index + 1:])

                rating_table = self.__make_table(value, key)
                self.__console.print(rating_table, '\n')
        else:
            self.__error_panel(rating[1])

        self.__back()

    def __show_login_password(self, show_password=False):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype(end='\n')

        login = self.__json_manager.get_data('user_data.json')['login']
        password = self.__json_manager.get_data('user_data.json')['password']

        input_color = next(
            value for key, value in self.__settings_object._settings["selection_menu"] if key == 'answer'
        )

        self.__console.print(f'[{self.__settings_object._settings["input"]}]* Логин: '
                             f'[{input_color}]{login}')

        if not show_password:
            if self.__settings_object._settings['show_password_menu_style'] == 'encrypted':
                password = list(password)
                random.shuffle(password)
                password = ''.join(password)
                self.__console.print(f'[{self.__settings_object._settings["input"]}]* Пароль: '
                                     f'[{input_color}]{password}')
            else:
                self.__console.print(f'[{self.__settings_object._settings["input"]}]* Пароль: '
                                     f'[{input_color}]'
                                     f'{self.__settings_object._settings["show_password_menu_style"] * 10}')

            style = questionary.Style(self.__settings_object._settings['selection_menu'])
            try:
                show = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'select',
                            'name': 'show_password',
                            'qmark': '',
                            'message': '',
                            'choices': ['Показать пароль', 'НАЗАД'],
                            'style': style,
                            'pointer': self.__settings_object._settings['menu_pointer_style']
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )['show_password']

                if show == 'Показать пароль':
                    self.__show_login_password(show_password=True)
                else:
                    self.__menu()
            except KeyboardInterrupt:
                return self.exit_app()
        else:
            password = self.__crypto_password(password)
            self.__console.print(f'[{self.__settings_object._settings["input"]}]* Пароль: '
                                 f'[{input_color}]{password}')

        self.__back()

    def __settings(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        settings_menu = self.__settings_menu.main_menu(self.__logotype)
        if not settings_menu:
            self.__menu()

    def __logout(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.__logotype()

        self.__warning_panel(
            'Дождитесь завершения выхода из аккаунта...\n'
            'ПОЖАЛУЙСТА, НЕ ЗАКРЫВАЙТЕ ПРОГРАММУ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК'
        )

        self.__json_manager.remove_file('user_data.json')
        self.__account.logout()
        self.run()

    """ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ """
    def __logotype(self, end=''):
        if self.__settings_object._settings['show_logo'] == 'true':
            self.__console.print(Panel(
                Align.center(text2art('STUDENT ACCOUNT', font=self._LOGO_FONT)[:-1]),
                highlight=False,
                style=self.__settings_object._settings['logo_color'],
                box=self.__settings_object._settings['logo_box_style'],
                safe_box=True)
            )

            if end:
                self.__console.print(end)

    def __make_table(self, data: list, table_name=None):
        table = Table(
            title=table_name,
            title_style='bold pale_green1',
            style=self.__settings_object._settings['table_color'],
            box=self.__settings_object._settings['table_box_style'],
            header_style=self.__settings_object._settings['table_header_color'],
            show_lines=True,
            safe_box=True,
            expand=True
        )

        for column in data[0]:
            table.add_column(column.replace(':', ''), justify='center', vertical='middle')
        for row in data[1:]:
            table.add_row(*row)

        return table

    @staticmethod
    def __crypto_password(password: str, encrypt: bool = False):
        secret = 'supER_MeGa_SEcrit112'

        kdf = PBKDF2HMAC(algorithm=SHA256(), length=32, salt=b'ABOBA123', iterations=100000)
        key = urlsafe_b64encode(kdf.derive(secret.encode()))
        cipher = Fernet(key)

        if encrypt:
            return cipher.encrypt(password.encode()).decode()
        else:
            return cipher.decrypt(password.encode()).decode()

    @staticmethod
    def create_log(logger_name: str, exception: str):
        os.makedirs('logs', exist_ok=True)
        log_files = os.listdir('logs')
        if len(log_files) > 10:
            for file in log_files:
                os.remove(f'logs/{file}')

        time_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)

        file_handler = logging.FileHandler(f'logs/{time_now}_ERROR.log')
        file_handler.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(name)s -> %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        logger.error(str(exception), exc_info=True)

        file_handler.close()
        logger.removeHandler(file_handler)

    """ ПАНЕЛИ | Panel() | ВЫВОДА СООБЩЕНИЙ """
    def __print_panel(self, panel, started, ended):
        if started:
            self.__console.print(started, end='')
        self.__console.print(panel)
        if ended:
            self.__console.print(ended, end='')

    def __inf_panel(self, text, start='', end='', center=False):
        if center:
            panel = Panel(
                Text(text, justify='center'),
                style=f'bold {self.__settings_object._settings["information"]}',
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True
            )
        else:
            panel = Panel(
                text,
                style=f'bold {self.__settings_object._settings["information"]}',
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True
            )

        self.__print_panel(panel, start, end)

    def __warning_panel(self, text, start='', end=''):
        panel = Panel(
            text,
            style=f'bold {self.__settings_object._settings["warning"]}',
            box=self.__settings_object._settings['messages_box_style'],
            safe_box=True,
            expand=True
        )

        self.__print_panel(panel, start, end)

    def __error_panel(self, text, important=False, start='', end=''):
        if not important:
            panel = Panel(
                text,
                style=f'bold {self.__settings_object._settings["error"]}',
                title=f'[bold {self.__settings_object._settings["error"]}]ОШИБКА',
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True,
                expand=True
            )
        else:
            try:
                panel = Panel(
                    text,
                    style=f'bold {self.__settings_object._settings["error"]}',
                    title=f'[bold {self.__settings_object._settings["error"]}]ОШИБКА',
                    box=self.__settings_object._settings['messages_box_style'],
                    safe_box=True,
                    expand=True
                )
            except AttributeError:
                panel = Panel(
                    text,
                    style='bold #ff4d4d',
                    title='[bold #ff4d4d]ОШИБКА',
                    box=HEAVY,
                    expand=True
                )

        self.__print_panel(panel, start, end)

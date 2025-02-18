from src.utils import JSONManager
from .console_account_settings import ConsoleAppSettings
from .styles import boxes

import os
from typing import Callable, Type, Union

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text


class SettingsMenu(ConsoleAppSettings):
    __json_manager: JSONManager

    def __init__(self, console: Console, settings_object: ConsoleAppSettings, exit_app: Callable):
        super().__init__()
        self.__console = console
        self.__settings_object = settings_object
        self.__exit_app = exit_app
        self.__json_manager = JSONManager('data', create=True)

    def main_menu(self, logotype: Callable):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        self.__console.print(
            Panel(
                Text('НАСТРОЙКИ ОБНОВЛЯЮТСЯ ПРИ НАЖАТИИ "НАЗАД" ПОСЛЕ ИЗМЕНЕНИЯ НАСТРОЙКИ', justify='center'),
                style=self.__settings_object._settings['warning'],
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True,
                expand=True
            )
        )

        setting_choices = [
            'Изменить цвета элементов',
            'Изменить стили элементов',
            'Дополнительные настройки',
            'Посмотреть пользовательские настройки',
            'Сбросить все настройки',
            'НАЗАД'
        ]

        style = questionary.Style(self.__settings_object._settings['selection_menu'])

        menu_settings = questionary.unsafe_prompt(
            [
                {
                    'type': 'select',
                    'name': 'select_setting',
                    'qmark': '*',
                    'message': 'Что хотите изменить?',
                    'choices': setting_choices,
                    'style': style,
                    'pointer': self.__settings_object._settings['menu_pointer_style']
                }
            ],
            true_color=self.__settings_object._settings['true_color']
        )['select_setting']

        match menu_settings:
            case 'Изменить цвета элементов':
                self.__colors_menu(logotype)
            case 'Изменить стили элементов':
                self.__styles_menu(logotype)
            case 'Дополнительные настройки':
                self.__other_settings_menu(logotype)
            case 'Посмотреть пользовательские настройки':
                self.__show_user_settings(logotype)
            case 'Сбросить все настройки':
                self.__set_default_settings(logotype)
            case 'НАЗАД':
                return False

    def __colors_menu(self, logotype: Callable):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        element_choices = [
            'True Color [ Если неправильно отображается меню выбора ]',
            'Логотип',
            'Приветствующий блок [ Добро пожаловать, ... ]',
            'Ввод данных [ например, ввод предмета для поиска баллов ]',
            'Дополнительная информация',
            'Предупреждающее сообщение',
            'Сообщение об ошибке',
            'Значок перед вопросом в меню выбора',
            'Вопрос в меню выбора',
            'Ответ в меню выбора',
            'Элемент, на который указывает курсор в меню выбора',
            'Пункты в меню выбора',
            'Указатель в меню выбора',
            'Названия столбцов таблиц',
            'Рамки таблицы',
            'Я в таблице',
            'Линия-разделитель под таблицей [ Зачетная книжка ]',
            'НАЗАД'
        ]

        color = self.__make_menu('Цвет какого элемента хотите поменять?', element_choices)

        if color != 'НАЗАД':
            self.__new_color(logotype, color)
        elif color == 'НАЗАД':
            self.main_menu(logotype)

    def __styles_menu(self, logotype: Callable):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        element_choices = [
            'Рамки логотипа [ круглые/квадратный/двойные ]',
            'Рамки блоков сообщений [ например, предупреждающее сообщение ]',
            'Рамки приветствующего блока',
            'Рамки таблиц',
            'Символ-разделитель под таблицей [ Зачетная книжка ]',
            'Указатель в меню выбора [ стандартно: > ]',
            'Автозаполнение пароля при входе',
            'Пароль в пункте "Показать логин и пароль"',
            'НАЗАД'
        ]

        style = self.__make_menu('Стиль какого элемента хотите поменять?', element_choices)

        if style != 'НАЗАД':
            self.__new_style(logotype, style)
        elif style == 'НАЗАД':
            self.main_menu(logotype)

    def __other_settings_menu(self, logotype: Callable):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        element_choices = [
            'Показывать логотип',
            'Показывать приветствующий блок',
            'НАЗАД'
        ]

        if os.name != 'nt':
            element_choices.insert(2, 'Показывать предупреждение о правильном закрытии программы')

        user_settings = self.__make_menu('Что хотите поменять?', element_choices)

        if user_settings != 'НАЗАД':
            self.__new_other_setting(logotype, user_settings)
        elif user_settings == 'НАЗАД':
            self.main_menu(logotype)

    def __show_user_settings(self, logotype: Callable):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()
        user_settings = self.__settings_object._show_user_settings()

        if user_settings:
            user_settings = self.__json_manager.create_variable(user_settings)
        else:
            user_settings = Text('Пользовательских настроек не обнаружено', justify='center')

        self.__console.print(
            Panel(
                user_settings,
                style=self.__settings_object._settings['information'],
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True,
                expand=True
            )
        )

        self.__back(self.main_menu, logotype)

    def __new_color(self, logotype, element):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        self.__display_element(element)

        if 'True Color' in element:
            message = 'Настройка принимает значения [ TRUE, FALSE ]:'
            new_setting = self.__set_new_parameter(self.__colors_menu, element, message, logotype, bool)
        else:
            colors = ['#a1dffb', '#6ca0dc', '#bfa5ff', '#e8dff5', '#c7f9cc', '#d4ffb6', '#ffcc99', '#ffae5d', '#ff7a85']
            for index, color in enumerate(colors):
                self.__console.print(f'[bold white]{color} ' + f'[{color}]█' * (self.__console.width - len(color) - 1))
            self.__console.print()

            message = 'Введите цвет [ не обязательно из тех, что представлены выше ]:'
            new_setting = self.__set_new_parameter(self.__colors_menu, element, message, logotype, str)

        if new_setting is True:
            self.__back(self.__colors_menu, logotype)

    def __new_style(self, logotype, element):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        if 'Рамк' in element:
            tables = []
            tables_width = 0

            for name, box in boxes.items():
                table = Table(title=name, box=box)
                table.add_column('Header 1')
                table.add_column('Header 2')
                table.add_row('Cell', 'Cell')
                table.add_row('Cell', 'Cell', end_section=True)
                table.add_row('Footer1', 'Footer2')

                tables.append(table)
                tables_width += 30

                if tables_width >= self.__console.width:
                    self.__console.print(
                        Columns(
                            tables.copy(),
                            expand=True,
                            align='center',
                            width=25,
                            padding=0
                        )
                    )

                    tables = []
                    tables_width = 0

            if tables:
                self.__console.print(
                    Columns(
                        tables.copy(),
                        expand=True,
                        align='center',
                        width=25,
                        padding=0
                    )
                )

            message = 'Выберите рамку из предложенных выше:'
        elif 'Указател' in element:
            message = 'Указателем может быть совершенно любой символ:'
        elif 'Символ-разделитель' in element:
            message = 'Разделителем может быть совершенно любой символ:'
        else:
            message = 'Введите символ, который будет скрывать пароль [ encrypted = в зашифрованном пароль ]:'

        new_settings = self.__set_new_parameter(self.__styles_menu, element, message, logotype, str)
        if new_settings is True:
            self.__back(self.__styles_menu, logotype)

    def __new_other_setting(self, logotype, element):
        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        message = 'Настройка принимает значения [ TRUE, FALSE ]:'
        new_setting = self.__set_new_parameter(self.__other_settings_menu, element, message, logotype, bool)
        if new_setting is True:
            self.__back(self.__other_settings_menu, logotype)

    def __set_default_settings(self, logotype):
        self.__json_manager.remove_file('settings.json')
        self.__settings_object._update_settings()

        os.system('cls' if os.name == 'nt' else 'clear')
        logotype()

        self.__console.print(
            Panel(
                Text('НАСТРОЙКИ УСПЕШНО СБРОШЕНЫ', justify='center'),
                style=self.__settings_object._settings['warning'],
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True,
                expand=True
            )
        )

        self.__back(self.main_menu, logotype)

    """ ВСОПОМОГАТЕЛЬНЫЕ МЕТОДЫ """
    @staticmethod
    def get_setting_from_dict(setting):
        for key, value in settings.items():
            if setting == key:
                return value

    def __back(self, menu: Callable, logotype: Callable):
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

            menu(logotype)
        except KeyboardInterrupt:
            self.__exit_app()

    def __make_menu(self, message: str, choices: list):
        style = questionary.Style(self.__settings_object._settings['selection_menu'])

        menu = questionary.unsafe_prompt(
            [
                {
                    'type': 'select',
                    'name': 'menu',
                    'qmark': '*',
                    'message': message,
                    'choices': choices,
                    'style': style,
                    'pointer': self.__settings_object._settings['menu_pointer_style']
                }
            ],
            true_color=self.__settings_object._settings['true_color']
        )['menu']

        return menu

    def __display_element(self, element):
        self.__console.print(
            Panel(
                Text(element, justify='center'),
                style=self.__settings_object._settings['information'],
                box=self.__settings_object._settings['messages_box_style'],
                safe_box=True,
                expand=True
            )
        )

    def __set_new_parameter(self, menu, element, message, logotype, ask_type=Type[Union[str, bool]], repeated=False):
        try:
            main_style = questionary.Style(self.__settings_object._settings['selection_menu'])

            if ask_type == str:
                if not repeated:
                    self.__console.print(
                        Panel(
                            Text('Чтобы вернуться назад напишите "назад"\n'
                                 'Чтобы установить значение по умолчанию напишите "default"', justify='center'),
                            style=self.__settings_object._settings['warning'],
                            box=self.__settings_object._settings['messages_box_style'],
                            safe_box=True,
                            expand=True
                        )
                    )

                entered_setting = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'text',
                            'name': 'enter_setting',
                            'qmark': '*',
                            'message': message,
                            'style': main_style
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )['enter_setting']
            else:
                entered_setting = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'select',
                            'name': 'enter_setting',
                            'qmark': '*',
                            'message': message,
                            'choices': ['TRUE', 'FALSE', 'НАЗАД'],
                            'style': main_style,
                            'pointer': self.__settings_object._settings['menu_pointer_style']
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )['enter_setting'].lower()

            setting_name = self.get_setting_from_dict(element)

            if entered_setting.upper() in ('НАЗАД', 'BACK'):
                return menu(logotype)
            elif entered_setting.upper() == 'DEFAULT':
                self.__settings_object._one_default_setting(setting_name)
            elif not entered_setting:
                pass
            else:
                setting = {setting_name: entered_setting}
                self.__json_manager.write_data('settings.json', setting)

            self.__settings_object._update_settings()

            if ask_type == str:
                confirm_style = questionary.Style(self.__settings_object._settings['selection_menu'])
                entered_setting = questionary.unsafe_prompt(
                    [
                        {
                            'type': 'select',
                            'name': 'enter_setting',
                            'qmark': '*',
                            'message': 'Применить новое значение?',
                            'choices': ['Применить', 'Ввести другое значение'],
                            'style': confirm_style,
                            'pointer': self.__settings_object._settings['menu_pointer_style']
                        }
                    ],
                    true_color=self.__settings_object._settings['true_color']
                )['enter_setting']

                if entered_setting == 'Применить':
                    pass
                else:
                    return self.__set_new_parameter(menu, element, message, logotype, ask_type, True)

            return True
        except KeyboardInterrupt:
            self.__exit_app()


""" ВСЕ НАСТРОЙКИ, КОТОРЫЕ ЕСТЬ В ПРОГРАММЕ """
settings = {
    'True Color [ Если неправильно отображается меню выбора ]': 'true_color',    # <------------------> ЦВЕТА
    'Логотип': 'logo_color',
    'Приветствующий блок [ Добро пожаловать, ... ]': 'user_name_box_color',
    'Ввод данных [ например, ввод предмета для поиска баллов ]': 'input',
    'Дополнительная информация': 'information',
    'Предупреждающее сообщение': 'warning',
    'Сообщение об ошибке': 'error',
    'Значок перед вопросом в меню выбора': 'qmark',
    'Вопрос в меню выбора': 'question',
    'Ответ в меню выбора': 'answer',
    'Элемент, на который указывает курсор в меню выбора': 'highlighted',
    'Пункты в меню выбора': 'text',
    'Указатель в меню выбора': 'pointer',
    'Названия столбцов таблиц': 'table_header_color',
    'Рамки таблицы': 'table_color',
    'Я в таблице': 'me_in_table_color',
    'Линия-разделитель под таблицей [ Зачетная книжка ]': 'split_table_line_color',
    'Рамки логотипа [ круглые/квадратный/двойные ]': 'logo_box_style',    # <------------------> СТИЛИ
    'Рамки блоков сообщений [ например, предупреждающее сообщение ]': 'messages_box_style',
    'Рамки приветствующего блока': 'welcome_box_style',
    'Рамки таблиц': 'table_box_style',
    'Символ-разделитель под таблицей [ Зачетная книжка ]': 'split_table_symbol_style',
    'Указатель в меню выбора [ стандартно: > ]': 'menu_pointer_style',
    'Автозаполнение пароля при входе': 'password_style',
    'Пароль в пункте "Показать логин и пароль"': 'show_password_menu_style',
    'Показывать логотип': 'show_logo',    # <------------------> ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
    'Показывать приветствующий блок': 'welcome_message',
    'Показывать предупреждение о правильном закрытии программы': 'warning_about_exit'
}

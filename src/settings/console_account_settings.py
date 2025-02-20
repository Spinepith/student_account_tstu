from src.utils import JSONManager
from .colors import Colors
from .styles import Styles, boxes
from .other_settings import OtherSettings


class ConsoleAppSettings:
    __json_manager = JSONManager()

    """
        КОНСТАНТНЫЕ НАСТРОЙКИ, КОТОРЫЕ ПОЛЬЗОВАТЕЛЬ НЕ ВИДИТ И НЕ МОЖЕТ ПОМЕНЯТЬ
        Т.К. ОНИ НЕИЗМЕНЯЕМЫЕ - ПРИНАДЛЕЖАТ САМОМУ КЛАССУ <---------
    """
    _LOGO_FONT = 'small'

    """
        НАСТРОЙКИ, КОТОРЫЕ ПОЛЬЗОВАТЕЛЬ МОЖЕТ КАСТОМИЗИРОВАТЬ
        Т.К. ЭТИ НАСТРОЙКИ МОГУТ БЫТЬ ИЗМЕНЕНЫ, ПОЭТОМУ ПРИНАДЛЕЖАТ ОБЪЕКТУ <---------
    """
    def __init__(self, default_settings=False):
        self.__colors = Colors.get_colors()
        self.__styles = Styles.get_styles()
        self.__other_settings = OtherSettings.get_settings()

        self._default_settings = self.__collect_all_settings()
        self.__hard_settings = self.__find_hard_settings()
        self._settings = self._default_settings.copy()

        if not default_settings:
            self.__json_manager.set_directory('data', create=True)
            self._settings = self.__check_user_settings()
            self.__hard_settings = self.__find_hard_settings(self._settings)

    def __collect_all_settings(self):
        default_settings = {}

        for key, value in self.__dict__.items():
            if key.startswith(f'_{__class__.__name__}__'):
                if 'colors' in key:
                    for setting_key, setting_value in value.items():
                        if setting_value == 'true':
                            setting_value = True
                        elif setting_value == 'false':
                            setting_value = False
                        default_settings[setting_key] = setting_value
                else:
                    default_settings.update(value)

        return default_settings

    def __check_user_settings(self):
        try:
            if self.__json_manager.find_file('settings.json'):
                user_settings = self.__json_manager.get_data('settings.json')

                for key, value in user_settings.items():
                    if key in self.__hard_settings and not isinstance(self.__hard_settings[key], list):
                        self._settings[key] = self.__parse_hard_setting(key, value)

                    elif key in self._settings and value != self._settings[key]:
                        self._settings[key] = value

                    elif key not in self.__hard_settings:
                        for element1, element2 in self.__hard_settings.items():
                            if isinstance(element2, list):
                                for old_key, old_value in element2:
                                    if old_key == key:
                                        self._settings[element1] = self.__parse_hard_setting(old_key, value, element1)

                return self._settings.copy()
        except AttributeError:
            raise AttributeError

        return self._default_settings.copy()

    def _update_settings(self):
        self._settings = self.__check_user_settings()
        self.__hard_settings = self.__find_hard_settings(self._settings)

    def _one_default_setting(self, setting):
        self._settings[setting] = self._default_settings[setting]

        pre_data = self.__json_manager.get_data('settings.json')
        post_data = {key: value for key, value in pre_data.items() if key != setting}
        self.__json_manager.write_data('settings.json', post_data, 'rewrite')

    def __find_hard_settings(self, settings: dict = None):
        hard_settings = {}

        if not settings:
            settings = self._default_settings

        for hard_key, hard_value in settings.items():
            if 'true_color' in hard_key:
                hard_settings[hard_key] = hard_value

            if 'box_style' in hard_key:
                hard_settings[hard_key] = hard_value

            if isinstance(hard_value, list):
                hard_settings[hard_key] = hard_value

        return hard_settings

    def __parse_hard_setting(self, key, value, list_key=None):
        hard_value = None

        for hard_key, hard_value in self.__hard_settings.items():
            if 'true_color' in key and hard_key == key:
                user_settings = self.__json_manager.get_data('settings.json')[hard_key]
                hard_value = True if user_settings in (True, 'true') else False
                self.__hard_settings[hard_key] = hard_value
                break

            if 'box_style' in key and hard_key == key:
                hard_value = next((box_value for box_key, box_value in boxes.items() if box_key == value), None)
                self.__hard_settings[hard_key] = hard_value
                break

            elif list_key and isinstance(self.__hard_settings[list_key], list):
                first_step = str(self.__hard_settings[list_key]).strip('[]')
                second_step = first_step.split('), (')
                third_step = [tuple(item.strip("()").replace("'", "").split(", ", 1)) for item in second_step]

                hard_value = [(old_key, value if old_key == key else old_value) for old_key, old_value in third_step]
                self.__hard_settings[list_key] = hard_value
                break

        if not hard_value:
            hard_value = self.__hard_settings[key]

        return hard_value

    """ МЕТОДЫ, КОТОРЫЕ РАСПОЛОЖЕНЫ НИЖЕ - ДЛЯ РАБОТЫ С МЕНЮ НАСТРОЕК """
    def _show_user_settings(self):
        if self.__json_manager.find_file('settings.json'):
            user_settings = self.__json_manager.get_data('settings.json')
            return user_settings
        return None

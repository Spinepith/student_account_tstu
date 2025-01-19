import json
import os


class JSONManager:
    __is_dir = False
    __directory: str
    __files: list

    def __init__(self, directory: str = None, create: bool = False):
        if directory:
            self.set_directory(directory, create)

    def set_directory(self, directory: str, create=False):
        if not os.path.exists(directory):
            if not create:
                raise FileNotFoundError
            os.makedirs(directory, exist_ok=True)

        self.__is_dir = True
        self.__directory = directory
        self.__files = [i for i in os.listdir(self.__directory) if i.endswith('.json')]

    def get_directory(self):
        if self.__directory:
            return self.__directory

    def get_files(self):
        if self.__is_dir:
            self.__update_dir()
            return self.__files

    def get_data(self, file: str):
        if not self.__is_dir:
            raise FileNotFoundError

        self.__update_dir()
        try:
            if file in self.__files:
                with open(f'{self.__directory}/{file}', 'r', encoding='UTF-8') as opened_file:
                    return json.load(opened_file)
        except (PermissionError, FileNotFoundError, json.JSONDecodeError):
            pass

    def write_data(self, file: str, data: dict, mode='update'):
        try:
            if mode == 'rewrite':
                old_data = data
            else:
                old_data = self.get_data(file) if self.find_file(file) else {}
                old_data.update(data)

            with open(f'{self.__directory}/{file}', 'w', encoding='UTF-8') as opened_file:
                json.dump(old_data, opened_file, ensure_ascii=False, indent=4)
        except (PermissionError, FileNotFoundError, json.JSONDecodeError):
            pass

    def find_file(self, file: str):
        self.__update_dir()
        return True if file in self.__files else False

    def remove_file(self, file: str):
        if not self.__is_dir:
            raise FileNotFoundError

        self.__update_dir()
        try:
            if file in self.__files:
                os.remove(f'{self.__directory}/{file}')
        except (PermissionError, FileNotFoundError):
            pass

    @staticmethod
    def create_variable(data: str):
        return json.dumps(data, indent=4, ensure_ascii=True)

    def __update_dir(self):
        self.__files = os.listdir(self.__directory)

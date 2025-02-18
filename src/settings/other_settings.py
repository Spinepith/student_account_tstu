class OtherSettings:
    __main = {
        'show_logo': 'true',
        'welcome_message': 'true',
        'warning_about_exit': 'true'
    }

    @classmethod
    def get_settings(cls):
        settings = {}

        for key, value in cls.__dict__.items():
            if not key.startswith('__') and isinstance(value, dict):
                settings.update(value)

        return settings

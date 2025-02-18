import os


class Colors:
    """ В ЭТОМ КЛАССЕ НАХОДЯТСЯ ВСЕ ЦВЕТА, КОТОРЫЕ ИСПОЛЬЗУЕТСЯ В ПРОГРАММЕ """
    __main = {
        'true_color': 'true' if os.name == 'nt' else 'false',
        'logo_color': '#8c8eff',
        'user_name_box_color': '#5f87ff'
    }

    __input_output = {
        'input': '#6aff6a',
        'information': '#5f87ff',
        'warning': '#ff884d',
        'error': '#ff4d4d',
    }

    __selection_menu = [
        ('qmark', '#6aff6a'),
        ('question', '#6aff6a'),
        ('answer', '#ffc76a'),
        ('highlighted', '#ffc76a'),
        ('text', '#ffddb6'),
        ("instruction", 'hidden'),
        ("pointer", '#ff6f61')
    ]

    __table = {
        'table_header_color': '#afff87',
        'table_color': '#4d89c7',
        'me_in_table_color': '#00875f',
        'split_table_line_color': '#8967B3'
    }

    @classmethod
    def get_colors(cls):
        colors = {}

        for key, value in cls.__dict__.items():
            if key.startswith('__'):
                continue

            elif 'selection_menu' in key or 'authorization_menu' in key:
                colors[key.removeprefix(f'_{cls.__name__}__')] = value

            elif isinstance(value, dict):
                colors.update(value)

        return colors

from rich.box import *


class Styles:
    """ В ЭТОМ КЛАССЕ НАХОДЯТСЯ ВСЕ СТИЛИ, КОТОРЫЕ ИСПОЛЬЗУЕТСЯ В ПРОГРАММЕ """
    __main = {
        'password_style': '*',
        'show_password_menu_style': '*',
        'logo_box_style': HEAVY,
        'messages_box_style': ROUNDED,
        'welcome_box_style': ROUNDED,
        'menu_pointer_style': '>',
        'table_box_style': ROUNDED,
        'split_table_symbol_style': '#'
    }

    @classmethod
    def get_styles(cls):
        styles = {}

        for key, value in cls.__dict__.items():
            if not key.startswith('__') and isinstance(value, dict):
                styles.update(value)

        return styles


boxes = {
    'ASCII': ASCII,
    'ASCII2': ASCII2,
    'ASCII_DOUBLE_HEAD': ASCII_DOUBLE_HEAD,
    'DOUBLE': DOUBLE,
    'DOUBLE_EDGE': DOUBLE_EDGE,
    'HEAVY': HEAVY,
    'HEAVY_EDGE': HEAVY_EDGE,
    'HEAVY_HEAD': HEAVY_HEAD,
    'HORIZONTALS': HORIZONTALS,
    'MARKDOWN': MARKDOWN,
    'MINIMAL': MINIMAL,
    'MINIMAL_DOUBLE_HEAD': MINIMAL_DOUBLE_HEAD,
    'MINIMAL_HEAVY_HEAD': MINIMAL_HEAVY_HEAD,
    'ROUNDED': ROUNDED,
    'SIMPLE': SIMPLE,
    'SIMPLE_HEAD': SIMPLE_HEAD,
    'SIMPLE_HEAVY': SIMPLE_HEAVY,
    'SQUARE': SQUARE,
    'SQUARE_DOUBLE_HEAD': SQUARE_DOUBLE_HEAD
}

def convert_settings_to_byte(settings: dict, mapping: dict) -> dict:

    def convert(setting, value):
        unit = mapping.get(setting)
        if unit is not None:
            if unit == 'B':
                return value * (1024**2)
            elif unit == 'KB':
                return value * 1024
        return value

    return {setting: convert(setting, value) for setting, value in settings.items()}


def convert_settings_to_mega_byte(settings: dict, mapping: dict) -> dict:

    def convert(setting, value):
        unit = mapping.get(setting)
        if unit is not None:
            if unit == 'B':
                return value // (1024**2)
            elif unit == 'KB':
                return value // 1024
        return value

    return {setting: convert(setting, value) for setting, value in settings.items()}

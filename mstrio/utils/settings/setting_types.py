import warnings

import mstrio.utils.helper as helper


class SettingValueFactory():

    def get_setting(self, config: dict) -> "SettingValue":
        setting_value_types = {
            'number': NumberSetting,
            'string': StringSetting,
            'enum': EnumSetting,
            'boolean': BoolSetting,
            'time': TimeSetting,
            'email': EmailSetting,
            'object': ObjectSetting,
            'mstr_object': MstrObjectSetting,
            None: DeprecatedSetting
        }
        setting_type = config.get('type')
        return setting_value_types[setting_type](config)


class SettingValue:
    """Base Settings Value class.

    It represents single setting configuration.
    """

    def __init__(self, config: dict):
        self.value = None
        self.name = config.get('name')
        self.description = config.get('description')
        self.reboot_rule = config.get('reboot_rule')
        self.multi_select = config.get('multi_select')
        self.options = config.get('options', [])
        self.relationship = config.get('relationship')

    def __repr__(self):
        return str(self._get_value())

    def __setattr__(self, name, value):
        """Setattr that allows setting valid name values defined in options."""
        # if setting the value of setting and options are defined
        # and value is str (option name)
        value_is_option_name = isinstance(value, str) and value
        setting_val_with_options = name == 'value' and getattr(self, 'options', None)
        if setting_val_with_options and value_is_option_name:
            option_found = helper.filter_list_of_dicts(self.options, name=value)
            if option_found:
                value = option_found[0]['value']
        super().__setattr__(name, value)

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        return helper.validate_param_value(
            self.name, value, self.type, special_values=options, exception=exception
        )

    def _get_value(self):
        return self.value

    @property
    def info(self):
        return self.__dict__


class EnumSetting(SettingValue):
    """Representation of an Enum setting type."""
    # initially empty options that require additional action
    # to be available (e.g. creating a TimeZone object)
    _DYNAMICALLY_ADDED_OPTIONS = {'defaultTimezone': str}

    def __init__(self, config: dict):
        super().__init__(config)
        config_name = config.get('name')
        if config_name in self._DYNAMICALLY_ADDED_OPTIONS:
            self.type = self._DYNAMICALLY_ADDED_OPTIONS[config_name]
        else:
            self.type = list if self.multi_select else type(self.options[0]['value'])

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        if self.type == list:
            options.append('')
        return helper.validate_param_value(
            self.name, value, self.type, special_values=options, exception=exception
        )

    def _get_value(self):
        option_name = [
            option['name']
            for option in helper.filter_list_of_dicts(self.options, value=self.value)
        ]
        if len(option_name) == 1:
            return option_name[0]
        else:
            return option_name


class BoolSetting(SettingValue):
    """Representation of a Boolean setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else bool


class NumberSetting(SettingValue):
    """Representation of a Number setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else int
        self.max_value = config.get('max_value')
        self.min_value = config.get('min_value')
        self.unit = config.get('unit')

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        return helper.validate_param_value(
            self.name,
            value,
            self.type,
            self.max_value,
            self.min_value,
            options,
            exception=exception
        )


class StringSetting(SettingValue):
    """Representation of a String setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        return helper.validate_param_value(self.name, value, self.type, exception=exception)


class TimeSetting(SettingValue):
    """Representation of a Time setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        regex = r"^[1-2][0-9](:[0-5][0-9]){1,2}$"
        return helper.validate_param_value(
            self.name, value, str, regex=regex, exception=exception, valid_example='23:45'
        )


class EmailSetting(SettingValue):
    """Representation of a Email setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        regex = r"[^@]+@[^@]+\.[^@]+"
        return helper.validate_param_value(
            self.name,
            value,
            self.type,
            special_values=[''],
            regex=regex,
            exception=exception,
            valid_example='name@mail.com'
        )


class ObjectSetting(SettingValue):
    """Representation of an Object setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = str
        self.object_type = config.get('object_type')


class MstrObjectSetting(SettingValue):
    """Representation of an MstrObject setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = str
        self.object_type = config.get('object_type')


class DeprecatedSetting:
    """Representation of a Deprecated setting type."""

    def __init__(self, config: dict):
        self.value = None
        self.name = config.get('name')
        self.description = config.get('description')

    def _validate_value(self, value):
        msg = f"Setting '{self.name}' with value '{value}' is deprecated and is read-only"
        warnings.warn(msg, DeprecationWarning)
        return True

    def __repr__(self):
        return str(self._get_value())

    def _get_value(self):
        return self.value

    @property
    def info(self):
        return self.__dict__

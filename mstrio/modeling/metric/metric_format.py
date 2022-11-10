from dataclasses import dataclass
from enum import auto
import logging
from typing import Any, Dict, Optional, Union

from mstrio.connection import Connection
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable

logger = logging.getLogger(__name__)


@dataclass
class FormatProperty(Dictable):
    """Object that specifies a single format type and it's value

    Attributes:
        type (FormatType): specify what format type is to be set
        value (string): specify what value to set the specified format type to

    FormatType Values:
        Number Category - integer between 0 and 9, default is 9:
            0 - Fixed
            1 - Currency
            2 - Date
            3 - Time
            4 - Percent
            5 - Fraction
            6 - Scientific
            7 - Custom
            8 - Special
            9 - General
        Number Decimal Places - integer between 0 and 30, default is 0
        Number Thousand Separator - boolean (true or false), default is true
        Number Currency Symbol - string of 1-4 characters, default is $
        Number Currency Position - integer between 0 and 3, default is 0:
            0 - at the beginning, for example $10
            1 - at the end, for example 10$
            2 - at the beginning with extra space, for example $ 10
            3 - at the end with extra space, for example 10 $
        Number Format - string of maximum of 255 characters, default value is
            General, example value: ###0.00;[RED]-###0.00
        Number Negative Numbers - integer between 1 and 5, default is 3:
            1 - normal negative format, for example -10
            2 - red color represents negative, -10 would be 10 in red color
            3 - parentheses represent negative, -10 would be (10)
            4 - both red color and parentheses represent negative, -10 would be
                (10) in red color
            5 - minus sign and red color represent negative, -10 would be -10
                in red color
        Alignment Horizontal - integer between 1 and 5, default value is 1:
            1 - General
            2 - Left
            3 - Center
            4 - Right
            5 - Fill
        Alignment Vertical - integer between 1 and 3, default value is 1:
            1 - Top
            2 - Center
            3 - Bottom
        Alignment Text Wrap - boolean (true or false), default is false
        Alignment Text Direction - allowed values are -90, 0 and 90
        Padding Left - double between 0.0 and 100.0, default value is 1.0
        Padding Right - double between 0.0 and 100.0, default value is 1.0
        Padding Top - double between 0.0 and 100.0, default value is 1.0
        Padding Bottom - double between 0.0 and 100.0, default value is 1.0
        Font Name - string representing font, default is Arial, if provided
            font name does not exist or is not supported, default is used
        Font Bold - boolean (true or false), default is false
        Font Italic - boolean (true or false), default is false
        Font Size - integer between 1 and 2147483647, recommended usable range
            is between 8 and 72, other font sizes might render format unreadable
        Font Strikeout - boolean (true or false), default is false
        Font Underline - boolean (true or false), default is false
        Font Color - FormatProperty.Color object representing font color in hex,
            RGB and server readable formats
        Font Script - integer between 1 and 2147483647, default value is 0,
            value represents corresponding font script, if the value has no
            corresponding script, the default will be used
        Border Top Style - integer between 0 and 6, default value is 1:
            0 - empty border
            1 - thin border
            2 - hair border
            3 - dashed border
            4 - dotted border
            5 - thick border
            6 - double border
        Border Right Style - the same rules as Top Style
        Border Left Style - the same rules as Top Style
        Border Bottom Style - the same rules as Top Style
        Border Top Color - FormatProperty.Color object representing border top
         color in hex, RGB and server readable formats
        Border Right Color - FormatProperty.Color object representing border
            right color in hex, RGB and server readable formats
        Border Left Color - FormatProperty.Color object representing border
            left color in hex, RGB and server readable formats
        Border Bottom Color - FormatProperty.Color object representing border
            bottom color in hex, RGB and server readable formats
        Background Fill Style - integer between 0 and 3, default value is 0:
            0 - solid, only has fill color
            1 - transparent
            2 - gradient, has fill color and gradient color
            3 - pattern, has fill color and gradient color
        Background Fill Color - FormatProperty.Color object representing
            background fill color in hex, RGB and server readable formats
        Background Pattern Color - FormatProperty.Color object representing
            background fill color in hex, RGB and server readable formats
        Background Pattern Style - integer between 1 and 18, default value is 1
        Background Gradient Color - FormatProperty.Color object representing
            background gradient color in hex, RGB and server readable formats
        Background Gradient Angle - allowed values are -90, 0 and 90
        Gradient X Offset - allowed values are 0, 50 and 100
        Gradient Y Offset - allowed values are 0, 50 and 100
    """

    class FormatType(AutoName):
        NUMBER_CATEGORY = auto()
        NUMBER_DECIMAL_PLACES = auto()
        NUMBER_THOUSAND_SEPARATOR = auto()
        NUMBER_CURRENCY_SYMBOL = auto()
        NUMBER_CURRENCY_POSITION = auto()
        NUMBER_FORMAT = auto()
        NUMBER_NEGATIVE_NUMBERS = auto()
        ALIGNMENT_HORIZONTAL = auto()
        ALIGNMENT_VERTICAL = auto()
        ALIGNMENT_TEXT_WRAP = auto()
        ALIGNMENT_TEXT_DIRECTION = auto()
        PADDING_LEFT = auto()
        PADDING_RIGHT = auto()
        PADDING_TOP = auto()
        PADDING_BOTTOM = auto()
        FONT_NAME = auto()
        FONT_BOLD = auto()
        FONT_ITALIC = auto()
        FONT_SIZE = auto()
        FONT_STRIKEOUT = auto()
        FONT_UNDERLINE = auto()
        FONT_COLOR = auto()
        FONT_SCRIPT = auto()
        BORDER_TOP_STYLE = auto()
        BORDER_LEFT_STYLE = auto()
        BORDER_BOTTOM_STYLE = auto()
        BORDER_RIGHT_STYLE = auto()
        BORDER_TOP_COLOR = auto()
        BORDER_LEFT_COLOR = auto()
        BORDER_BOTTOM_COLOR = auto()
        BORDER_RIGHT_COLOR = auto()
        BACKGROUND_FILL_COLOR = auto()
        BACKGROUND_PATTERN_COLOR = auto()
        BACKGROUND_PATTERN_STYLE = auto()
        BACKGROUND_FILL_STYLE = auto()
        BACKGROUND_GRADIENT_COLOR = auto()
        BACKGROUND_GRADIENT_ANGLE = auto()
        BACKGROUND_GRADIENT_X_OFFSET = auto()
        BACKGROUND_GRADIENT_Y_OFFSET = auto()

    @dataclass
    class Color(Dictable):
        """A class containing information about the color in different formats.
         It is used as a value for `FormatProperties` that type related
         with colors.

        Attributes:
            hex_value(str): color expressed in hex format (e.g. '#ff02ef')
            server_value(str): color translated for server readable format
            red(str): red component of a RGB format, expressed as decimal
            green(str): green component of a RGB format, expressed as decimal
            blue(str): blue component of a RGB format, expressed as decimal"""

        def _rgb_base_converter(
            self, r: str, g: str, b: str, original_base: int, desired_base: int
        ):
            format_spec = {2: '0>8b', 10: '', 16: '0>2x'}
            return (
                format(int(r, original_base), format_spec[desired_base]),
                format(int(g, original_base), format_spec[desired_base]),
                format(int(b, original_base), format_spec[desired_base]),
            )

        def _init_from_hex(self, hex_val: str) -> str:
            r, g, b = self._rgb_base_converter(r=hex_val[1:3], g=hex_val[3:5], b=hex_val[5:7],
                                               original_base=16, desired_base=2)
            self.server_value = str(int(r + g + b, 2))
            self.hex_value = hex_val
            self.red, self.green, self.blue = self._rgb_base_converter(r, g, b, 2, 10)

        def _init_from_rest(self, rest_val: str) -> str:
            bin_color = format(int(rest_val), '0>24b')
            r, g, b = self._rgb_base_converter(r=bin_color[0:8], g=bin_color[8:16],
                                               b=bin_color[16:24], original_base=2,
                                               desired_base=16)
            self.server_value = rest_val
            self.hex_value = f'#{r}{g}{b}'
            self.red, self.green, self.blue = self._rgb_base_converter(r, g, b, 16, 10)

        def _init_from_rgb(self, red: str, green: str, blue: str) -> str:
            r, g, b = self._rgb_base_converter(r=red, g=green, b=blue, original_base=10,
                                               desired_base=2)
            self.server_value = str(int(r + g + b, 2))
            r, g, b = self._rgb_base_converter(r=red, g=green, b=blue, original_base=10,
                                               desired_base=16)
            self.hex_value = f'#{r}{g}{b}'
            self.red, self.green, self.blue = red, green, blue

        hex_value: str
        server_value: str
        red: str
        green: str
        blue: str

        def __init__(
            self,
            hex_value: str | None = None,
            red: int | None = None,
            green: int | None = None,
            blue: int | None = None,
            server_value: str | None = None
        ):
            """Create an object representing color value of a `FormatProperty`.
             It can be created by providing either hex value, server readable
             value or all three RGB components. Two other representation will
             be generated automatically based on the one provided by the user.
             If more than one representation provided, priority goes as follows:
             server_value->hex_value->RGB values.

            Args:
                hex_value(str): color expressed in hex format (e.g. '#ff02ef')
                server_value(str): color translated for server readable format
                red(int): component of a RGB format, expressed as decimal
                green(int): component of a RGB format, expressed as decimal
                blue(int): component of a RGB format, expressed as decimal"""

            if server_value is not None and isinstance(server_value,
                                                       str) and server_value.isnumeric():
                self._init_from_rest(rest_val=server_value)
            elif hex_value is not None and hex_value[0] == '#' and len(hex_value) == 7:
                self._init_from_hex(hex_val=hex_value)
            elif red in range(256) and green in range(256) and blue in range(256):
                self._init_from_rgb(str(red), str(green), str(blue))
            else:
                raise ValueError('Invalid parameter for Color value of the format property.')

        def __repr__(self):
            return (
                f'hex_value: {self.hex_value}, rgb: ({self.red}, {self.green}, {self.blue}), '
                f'server_value: {self.server_value}'
            )

    _FROM_DICT_MAP = {
        'type': FormatType,
    }
    type: FormatType
    value: Union[str, "FormatProperty.Color"]

    def to_dict(self, camel_case: bool = True) -> dict:
        if isinstance(self.value, FormatProperty.Color):
            return {'type': self.type.value, 'value': self.value.server_value}
        return {'type': self.type.value, 'value': self.value}

    @classmethod
    def from_dict(
        cls,
        source: Dict[str, Any],
        connection: Optional["Connection"] = None,
        to_snake_case: bool = True
    ) -> "FormatProperty":
        if source.get('type'):
            if 'color' in source.get('type'):
                return FormatProperty(
                    type=FormatProperty.FormatType(source.get('type')),
                    value=FormatProperty.Color(server_value=source.get('value'))
                )
            return FormatProperty(
                type=FormatProperty.FormatType(source.get('type')), value=source.get('value')
            )


@dataclass
class MetricFormat(Dictable):
    """Object that specifies the formatting of the metric's values and headers

    Attributes:
        values (list[FormatProperty]): list of format properties for the values
            of the metric
        header (list[FormatProperty]): list of format properties for the header
            of the metric
    """

    _FROM_DICT_MAP = {
        'values': (
            lambda source,
            connection: [FormatProperty.from_dict(content, connection) for content in source]
        ),
        'header': (
            lambda source,
            connection: [FormatProperty.from_dict(content, connection) for content in source]
        ),
    }

    values: list[FormatProperty]
    header: list[FormatProperty]

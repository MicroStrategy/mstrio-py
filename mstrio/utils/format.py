from dataclasses import dataclass

from mstrio.utils.helper import Dictable


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
        r, g, b = self._rgb_base_converter(
            r=hex_val[1:3],
            g=hex_val[3:5],
            b=hex_val[5:7],
            original_base=16,
            desired_base=2,
        )
        self.server_value = str(int(r + g + b, 2))
        self.hex_value = hex_val
        self.red, self.green, self.blue = self._rgb_base_converter(r, g, b, 2, 10)

    def _init_from_rest(self, rest_val: str) -> str:
        bin_color = format(int(rest_val), '0>24b')
        r, g, b = self._rgb_base_converter(
            r=bin_color[0:8],
            g=bin_color[8:16],
            b=bin_color[16:24],
            original_base=2,
            desired_base=16,
        )
        self.server_value = rest_val
        self.hex_value = f'#{r}{g}{b}'
        self.red, self.green, self.blue = self._rgb_base_converter(r, g, b, 16, 10)

    def _init_from_rgb(self, red: str, green: str, blue: str) -> str:
        r, g, b = self._rgb_base_converter(
            r=red, g=green, b=blue, original_base=10, desired_base=2
        )
        self.server_value = str(int(r + g + b, 2))
        r, g, b = self._rgb_base_converter(
            r=red, g=green, b=blue, original_base=10, desired_base=16
        )
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
        server_value: str | None = None,
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

        if (
            server_value is not None
            and isinstance(server_value, str)
            and server_value.isnumeric()
        ):
            self._init_from_rest(rest_val=server_value)
        elif hex_value is not None and hex_value[0] == '#' and len(hex_value) == 7:
            self._init_from_hex(hex_val=hex_value)
        elif red in range(256) and green in range(256) and blue in range(256):
            self._init_from_rgb(str(red), str(green), str(blue))
        else:
            raise ValueError(
                'Invalid parameter for Color value of the format property.'
            )

    def __repr__(self):
        return (
            f'hex_value: {self.hex_value}, rgb: ({self.red}, {self.green}, '
            f'{self.blue}), server_value: {self.server_value}'
        )

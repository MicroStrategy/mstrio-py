import contextlib
import datetime as dt
from base64 import b64decode, b64encode

from pandas import DataFrame, Series
from pandas.api.types import is_datetime64_any_dtype


class Encoder:
    """Class handling base64 encoding and decoding of strings.

    As there are multiple instances of REST API requiring data to be encoded or
    being sent encoded so needed to be decoded, this helper class allows to do
    it consistently throughout mstrio-py.
    """

    _input: str = None
    _decoded_str: str = None
    _encoded_str: str = None

    def __init__(
        self,
        decoded_text: str | None = None,
        encoded_text: str | None = None,
    ) -> None:
        """Initialize Encoder object.

        Note:
            Provide either `encoded_text` or `decoded_text` but not both.

        Args:
            decoded_text (str, optional): Text to be encoded.
            encoded_text (str, optional): Text to be decoded.
        """
        if not bool(encoded_text) ^ bool(decoded_text):
            raise ValueError(
                "Provide either `encoded_text` or `decoded_text` but not "
                "both nor neither."
            )

        self._input = decoded_text or encoded_text

        if encoded_text:
            self._encoded_str = str(encoded_text)
            with contextlib.suppress(Exception):
                self._decoded_str = self.decode(self._encoded_str)
        else:
            self._decoded_str = str(decoded_text)
            try:
                temp = self.decode(self._decoded_str)
            except Exception:  # we expect fail
                temp = None
            finally:
                if temp:
                    # if did not fail and got value (aka successful decoding
                    # of allegedly already decoded text) -> fail
                    raise ValueError(
                        f"Provided decoded text '{self._decoded_str}' is "
                        "actually an encoded text"
                    )
            with contextlib.suppress(Exception):
                self._encoded_str = self.encode(self._decoded_str)

        if not self._decoded_str or not self._encoded_str:
            raise Exception(
                f"Provided text '{str(self._input)}' cannot be "
                f"properly {'decoded' if self._encoded_str else 'encoded'}"
            )

    @property
    def decoded_text(self) -> str:
        """Get decoded string."""
        return self._decoded_str

    @property
    def encoded_text(self) -> str:
        """Get encoded string."""
        return self._encoded_str

    @classmethod
    def is_encoded(cls, value: str) -> bool:
        """Check whether the provided string is base64-encoded."""
        if not value:
            return False
        try:
            return cls.encode(cls.decode(value)) == value
        except Exception:
            return False

    @staticmethod
    def decode(text: str) -> str:
        """Base64-decode a text string."""
        return b64decode(text.encode('utf-8')).decode('utf-8')

    @staticmethod
    def encode(text: str) -> str:
        """Base64-encode a text string."""
        return b64encode(text.encode('utf-8')).decode('utf-8')


class PandasDataframeEncoder:
    """Internal method for converting a Pandas DataFrame to Strategy One
    compliant base64 encoded JSON.

    When creating a data set, Strategy One APIs require the tabular data to
    have been transformed first into JSON and then into a base 64 encoded string
    before it is transmitted to the Intelligence Server via the REST API to
    create the data set. This class uses Pandas to handle transforming
    the DataFrame into a JSON representation of the data. For single-table data
    sets, Strategy One APIs require the JSON data to be formatted using
    the 'records' orientation from Pandas. Conversely, multi-table data sets
    require the JSON data to have a 'values' orientation. Based on the data set
    type, the correct encoding strategy is applied and the data is then encoded.

    Attributes:
        data_frame: Pandas DataFrame to be encoded.
        b64_data: DataFrame converted into a Base-64 encoded JSON string.
        orientation: For single-table data sets, "single"; for multi-table
            data sets, "multi".
    """

    def __init__(self, data_frame: DataFrame, dataset_type: str):
        """Inits Encoder with given data_frame and type.

        Args:
            data_frame (DataFrame): Pandas DataFrame to be converted.
            dataset_type (str): Dataset type. One of `single` or `multi` to
                correspond with single-table or multi-table sources.
        """
        self.data_frame: DataFrame = data_frame
        self._b64_data: str | None = None
        self.orientation: str | None = None
        # Mapping used when converting DataFrame rows
        # into proper JSON orientation needed for data uploads.
        _table_type_orient_map: dict = {'single': 'records', 'multi': 'values'}

        # Sets the proper orientation
        if dataset_type not in _table_type_orient_map:
            allowed_types = ', '.join(_table_type_orient_map)
            raise ValueError(f"Table type should be one of {allowed_types}")

        self.orientation = _table_type_orient_map[dataset_type]

    @staticmethod
    def _wrangle_date(x: Series) -> Series:
        if is_datetime64_any_dtype(x):
            return x
        if isinstance(x.iloc[0], dt.date):
            return x.astype('str')
        return x

    def encode(self) -> None:
        """Encode data in base 64."""
        self.data_frame = self.data_frame.apply(self._wrangle_date)

        json_data = self.data_frame.to_json(orient=self.orientation, date_format='iso')
        self._b64_data = Encoder(json_data).encoded_text

    @property
    def b64_data(self) -> str:
        if not self._b64_data:
            self.encode()
        return self._b64_data

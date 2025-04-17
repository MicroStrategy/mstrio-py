import datetime as dt
from base64 import b64encode

from pandas import DataFrame


class Encoder:
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

    def encode(self) -> None:
        """Encode data in base 64."""
        self.data_frame = self.data_frame.apply(
            lambda x: x.astype('str') if isinstance(x.iloc[0], dt.date) else x
        )

        json_data = self.data_frame.to_json(orient=self.orientation, date_format='iso')
        self._b64_data = b64encode(json_data.encode('utf-8')).decode('utf-8')

    @property
    def b64_data(self) -> str:
        if not self._b64_data:
            self.encode()
        return self._b64_data

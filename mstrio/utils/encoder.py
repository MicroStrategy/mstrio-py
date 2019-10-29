from base64 import b64encode


class Encoder(object):
    """Internal method for converting a Pandas DataFrame to MicroStrategy compliant base64 encoded JSON.

    When creating a data set, MicroStrategy APIs require the tabular data to have been transformed first into JSON and
    then into a base 64 encoded string before it is transmitted to the Intelligence Server via the REST API to create
    the data set. This class uses Pandas to handle transforming the DataFrame into a JSON representation of the data.
    For single-table data sets, MicroStrategy APIs require the JSON data to be formatted using the 'records' orientation
    from Pandas. Conversely, multi-table data sets require the JSON data to have a 'values' orientation. Based on the
    data set type, the correct encoding strategy is applied and the data is then encoded.

    Attributes:
        __b64_data: DataFrame converted into a Base-64 encoded JSON string.
        __orientation: For single-table data sets, "single"; for multi-table data sets, "multi".
        __table_type_orient_map: Mapping used when converting DataFrame rows into proper JSON orientation needed
            for data uploads.
    """

    __b64_data = None
    __orientation = None
    __table_type_orient_map = {"single": "records",
                               "multi": "values"}

    def __init__(self, data_frame, dataset_type):
        """Inits Encoder with given data_frame and type.

        Args:
            data_frame: Pandas DataFrame to be converted.
            dataset_type (str): Dataset type. One of `single` or `multi` to correspond with single-table or multi-table
                sources.

        """
        self.__data_frame = data_frame

        # Sets the proper orientation
        if dataset_type not in self.__table_type_orient_map.keys():
            raise ValueError("Table type should be one of " + '%s' % ', '.join(map(str, self.__table_type_orient_map)))
        else:
            self.__orientation = self.__table_type_orient_map[dataset_type]

    @property
    def encode(self):
        """Encode data in base 64."""
        self.__b64_data = b64encode(self.__data_frame.to_json(orient=self.__orientation,
                                                              date_format='iso').encode('utf-8')).decode('utf-8')
        # return base 64 encoded data to calling environment
        return self.__b64_data

from itertools import chain
from typing import TYPE_CHECKING

import pandas as pd

from mstrio.utils.helper import exception_handler

if TYPE_CHECKING:
    import numpy as np
else:
    np = pd.core.common.np


class Parser:
    """Converts JSON-formatted cube and report data into a tabular
    structure.

    Report data may store metrics in rows or columns. The result dataframe
    will always have metrics in columns.
    """

    AF_COL_SEP = "@"  # attribute form column label separator; commonly "@"
    chunk_size = None
    total_rows = None

    def __init__(self, response, parse_cube=True):
        self.parse_cube = parse_cube
        # row-level metric data
        self._metric_values_raw = []

        self.__set_modeling_axes(response=response)

        # extract column headers and names
        self._metric_col_names = self.__extract_metric_col_names(response=response)

        # attribute objects
        # extract attribute names
        self._attribute_names = self.__extract_attribute_names(response=response)

        # extract attribute form names
        self._attribute_elem_form_names = self.__extract_attribute_form_names(
            response=response
        )

        # parse attribute column names including attribute form names
        # into final column names
        self._attribute_col_names = self.__get_attribute_col_names()

        self.__extract_paging_info(response)

        # attribute data
        self._mapped_attributes = np.zeros(
            (0, len(self._attribute_col_names)), dtype=object
        )

    def parse(self, response):
        """
        Args:
            response: JSON-formatted content of API response.
        """
        if self.total_rows > 0:
            # extract attribute values into numpy 2D array if attributes exist
            # in the response
            if self._attribute_names:
                self._mapped_attributes = np.vstack(
                    (self._mapped_attributes, self.__map_attributes(response=response))
                )

            # extract metric values if metrics exist in the response
            if self._metric_col_names:
                self._metric_values_raw.extend(
                    self.__extract_metric_values(response=response)
                )

    def __to_dataframe(self):
        # create attribute data frame, then re-map integer array with
        # corresponding attribute element values
        attribute_df = pd.DataFrame(
            data=self._mapped_attributes, columns=self._attribute_col_names
        )

        # create metric values data frame
        metric_df = pd.DataFrame(
            data=self._metric_values_raw, columns=self._metric_col_names
        )

        return pd.concat([attribute_df, metric_df], axis=1)

    def __set_modeling_axes(self, response):
        """Extract modeling axes from response, i.e. metrics in rows or columns
        as indicated in the response and attributes in the other axis.
        """
        metric_position_dict = response["definition"]["grid"].get("metricsPosition")
        self.metric_axis = (
            metric_position_dict["axis"] if metric_position_dict else "columns"
        )
        self.attribute_axis = "rows" if self.metric_axis == "columns" else "columns"

    def __map_attributes(self, response):
        label_map = self.__create_attribute_element_map(response=response)
        row_index = self.__extract_attribute_element_row_index(response=response)
        row_index_array = np.array(row_index)
        _, columns = row_index_array.shape

        # create attribute form name to attribute form index mapping
        vfunc = np.vectorize(
            lambda attribute_indexes, columns: label_map[columns][attribute_indexes]
        )

        return vfunc(row_index_array, range(columns))

    def __create_attribute_element_map(self, response):
        """Create a map of type nested list for attribute element labels.

        The index of the list corresponds to attribute element row index from
        the grid headers. The map is used to map the integer-based grid
        header values to the real attribute element labels."""

        # extract attribute form and attribute elements labels
        rows = response["definition"]["grid"][self.attribute_axis]
        form_values_rows = [
            [el['formValues'] for el in row['elements']] for row in rows
        ]

        def replicate_form_values(form_values):
            """Replicate attribute element values for total, count, etc. to fill
            the lists to correct size. I-Server only sends them once per
            attribute"""
            if self.parse_cube:
                return

            for i, attr in enumerate(self._attribute_elem_form_names):
                required_len = len(attr)

                for r in form_values[i]:
                    if len(r) < required_len:
                        r.extend(r * (required_len - 1))

        def separate(form_values):
            """Format into correct list structure. This function separates the
            nested lists into a list of list where one element corresponds to an
            attribute column"""
            final_list = []
            try:
                for attr in form_values:
                    row = len(attr[0])
                    col = len(attr)
                    final_list.extend(
                        np.array(attr).reshape(col, row).transpose().tolist()
                    )
                return final_list
            except IndexError:
                msg = (
                    "Missing attribute elements, please check if attribute elements IDs"
                    " are valid and if they exist in report."
                )
                exception_handler(msg, IndexError)

        replicate_form_values(form_values_rows)
        ae_index_map = separate(form_values_rows)

        return ae_index_map

    def __extract_attribute_element_row_index(self, response):
        """Extract the attribute element index for each row from the headers."""

        # Read list of attribute element indexes. Each entry in the list
        # corresponds to one row in the dataframe and has as many indexes as
        # there are attributes, e.g. entry [0, 13] means 0th element of first
        # attribute and 13th element of second attribute
        attribute_headers = response["data"]["headers"][self.attribute_axis]
        if self.metric_axis == "rows":
            # transpose
            attribute_headers = np.array(attribute_headers).T.tolist()

        # For each row in the dataframe, repeat each attribute element index
        # as many times as there are attribute forms for that attribute
        return [
            list(
                chain.from_iterable(
                    [
                        [r for _ in f]
                        for r, f in zip(row, self._attribute_elem_form_names)
                    ]
                )
            )
            for row in attribute_headers
        ]

    def __extract_paging_info(self, response):
        # extract paging info
        self.chunk_size = response["data"]["paging"]["limit"]
        self.total_rows = response["data"]["paging"]["total"]

    def __extract_metric_values(self, response):
        raw_values = response["data"]["metricValues"]["raw"]
        if self.metric_axis == "rows":
            # transpose
            raw_values = np.array(raw_values).T.tolist()
        return raw_values

    def __extract_metric_col_names(self, response):
        if response["definition"]["grid"][self.metric_axis]:
            return [
                i['name']
                for i in response["definition"]["grid"][self.metric_axis][-1][
                    "elements"
                ]
            ]
        else:
            return []

    def __extract_attribute_form_names(self, response):
        # extract attribute form names
        return [
            [form["name"] for form in attribute["forms"]]
            for attribute in response["definition"]["grid"][self.attribute_axis]
        ]

    def __extract_attribute_names(self, response):
        return [
            attribute["name"]
            for attribute in response["definition"]["grid"][self.attribute_axis]
        ]

    def __get_attribute_col_names(self):
        # extract and format attribute form column labels
        col_names = []
        for attr, forms in zip(self._attribute_names, self._attribute_elem_form_names):
            if len(forms) == 1:
                # if only one form, do not display the attribute form type
                # in the column headers
                col_names.append(attr)
            else:
                # otherwise concatenate the attribute name, separator,
                # and form type
                for form in forms:
                    col_names.append(attr + self.AF_COL_SEP + form)

        return col_names

    def has_multiform_attributes(self):
        return any(len(item) > 1 for item in self._attribute_elem_form_names)

    @property
    def dataframe(self):
        return self.__to_dataframe()

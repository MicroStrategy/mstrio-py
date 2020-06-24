import pandas as pd
import numpy as np
from itertools import chain

from mstrio.utils.helper import exception_handler

class Parser:
    """
    Converts JSON-formatted cube and report data into a tabular structure
    """

    AF_COL_SEP = "@"  # attribute form column label separator; commonly "@"
    chunk_size = None
    total_rows = None

    def __init__(self, response, parse_cube=True):

        self.parse_cube = parse_cube
        # row-level metric data
        self._metric_values_raw = []

        # extract column headers and names
        self._metric_col_names = self.__extract_metric_col_names(response=response)

        # attribute objects
        # extract attribute names
        self._attribute_names = self.__extract_attribute_names(response=response)

        # exract attribute form names
        self._attribute_elem_form_names = self.__extract_attribute_form_names(response=response)

        # parse attribute column names including attribute form names into final column names
        self._attribute_col_names = self.__get_attribute_col_names()

        self.__extract_paging_info(response)

        # attribute data
        self._mapped_attributes = np.zeros((0, len(self._attribute_col_names)), dtype=object)

    def parse(self, response):
        """
        :param response: JSON-formatted content of API response.
        """
        if self.total_rows > 0:
            # extract attribute values into numpy 2D array if attributes exist in the response
            if self._attribute_names:
                self._mapped_attributes = np.vstack((self._mapped_attributes, self.__map_attributes(response=response)))

            # extract metric values if metrics exist in the response
            if self._metric_col_names:
                self._metric_values_raw.extend(self.__extract_metric_values(response=response))

    def __to_dataframe(self):

        # create attribute data frame, then re-map integer array with corresponding attribute element values
        attribute_df = pd.DataFrame(
            data=self._mapped_attributes, columns=self._attribute_col_names)

        # create metric values data frame
        metric_df = pd.DataFrame(
            data=self._metric_values_raw, columns=self._metric_col_names)

        return pd.concat([attribute_df, metric_df], axis=1)

    def __map_attributes(self, response):

        # def map_index(attribute_indexes, columns):
        #     return label_map[columns][attribute_indexes]
        label_map = self.__create_attribute_element_map(response=response)
        row_index = self.__extract_attribute_element_row_index(response=response)
        row_index_array = np.array(row_index)
        _, columns = row_index_array.shape

        # create attribute form name to attribute form index mapping
        vfunc = np.vectorize(lambda attribute_indexes, columns: label_map[columns][attribute_indexes])

        return vfunc(row_index_array, range(columns))

    def __create_attribute_element_map(self, response):
        # creates a map of type nested list for attribute element labels. The index of the list corresponds to
        # attribute element row index from the grid headers. The map is used later to map the integer-based grid
        # header values to the real attribute element labels

        # extract attribute form and attribute elements labels
        rows = response["definition"]["grid"]["rows"]
        form_values_rows = [[el['formValues'] for el in row['elements']] for row in rows]

        def replicate_form_values(form_values):
            # replicate attribute element values for total, count, etc. to fill the lists to correct size
            # I-Server only sends them once for attribute
            if not self.parse_cube:
                for i, attr in enumerate(self._attribute_elem_form_names):

                    required_len = len(attr)

                    for r in form_values[i]:
                        if len(r) < required_len:
                            r.extend(r * (required_len - 1))

        def separate(form_values):
            # format into correct list structure. This function separates the nested lists into a list of list
            # where one element corresponds to a attribute column
            final_list = []
            try:
                for attr in form_values:
                    row = len(attr[0])
                    col = len(attr)
                    final_list.extend(np.array(attr).reshape(col, row).transpose().tolist())
                return final_list
            except IndexError as e:
                exception_handler("Missing attribute elements, please check if attribute elements IDs are valid and if they exist in report.",
                                  type(e))

        replicate_form_values(form_values_rows)
        ae_index_map = separate(form_values_rows)

        return ae_index_map

    def __extract_attribute_element_row_index(self, response):
        # extracts the attribute element row index from the headers
        return [list(chain.from_iterable([[r for _ in f] for r, f in zip(row, self._attribute_elem_form_names)]))
                for row in response["data"]["headers"]["rows"]]

    def __extract_paging_info(self, response):
        # extract paging info
        self.chunk_size = response["data"]["paging"]["limit"]
        self.total_rows = response["data"]["paging"]["total"]

    @staticmethod
    def __extract_metric_values(response):
        return response["data"]["metricValues"]["raw"]

    @staticmethod
    def __extract_metric_col_names(response):
        if response["definition"]["grid"]["columns"]:
            return [i['name'] for i in response["definition"]["grid"]["columns"][-1]["elements"]]
        else:
            return []

    @staticmethod
    def __extract_attribute_form_names(response):
        # extract attribute form names
        return [[e["name"] for e in i["forms"]] for i in response["definition"]["grid"]["rows"]]

    @staticmethod
    def __extract_attribute_names(response):
        return [i["name"] for i in response["definition"]["grid"]["rows"]]

    def __get_attribute_col_names(self):
        # extract and format attribute form column labels
        col_names = []
        for attr, forms in zip(self._attribute_names, self._attribute_elem_form_names):
            if len(forms) == 1:
                # if there is only one form, do not display the attribute form type in the column headers
                col_names.append(attr)
            else:
                # otherwise concatenate the attribute name, separator, and form type
                for form in forms:
                    col_names.append(attr + self.AF_COL_SEP + form)

        return col_names

    @property
    def dataframe(self):
        return self.__to_dataframe()

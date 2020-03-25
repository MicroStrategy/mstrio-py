import json
import pandas as pd
from tqdm.auto import tqdm

from mstrio.api import datasets
from mstrio.utils.model import Model
from mstrio.utils.encoder import Encoder


class Dataset:
    """Create and update data in MicroStrategy datasets.
    Iteratively build a dataset with `Dataset.add_table()`. Then, create the dataset using `Dataset.create()`. When
    updating data in the dataset, add individual tables to the dataset and define how the dataset should be updated
    on the MicroStrategy server, then call `Dataset.update().`
    Attributes:
        name: Name of the dataset.
        description: Description given to the dataset.
        dataset_id: Unique identifier for the dataset. Used to update a pre-existing dataset or generated after creating
            a new dataset.
        __upload_body: Body of the request used to describe the dataset update operation.
        _session_id: Identifies the data upload session.
    """

    __VALID_POLICY = ['add', 'update', 'replace', 'upsert']
    __MAX_DESC_LEN = 250

    def __init__(self, connection, name=None, description=None, dataset_id=None):
        """Interface for creating, updating, and deleting MicroStrategy in-memory datasets.
        When creating a new dataset, provide a dataset name and an optional description. When updating a pre-existing
        dataset, provide the dataset identifier. Tables are added to the dataset in an
        iterative manner using `add_table()`.
        Args:
            connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
            name (str): Name of the dataset.
            description (str, optional): Description of the dataset. Must be less than or equal to 250 characters.
            dataset_id (str, optional): Identifier of a pre-existing dataset. Used when updating a pre-existing dataset.
        """

        if name is not None:
            self.__check_param_str(name, msg="Dataset name should be a string.")
            self.__check_param_len(name,
                                   msg="Dataset name should be <= {} characters.".format(self.__MAX_DESC_LEN),
                                   length=self.__MAX_DESC_LEN)
        self._name = name

        if description is not None:
            self.__check_param_str(description, msg="Dataset description should be a string.")
            self.__check_param_str(description, msg="Dataset description should be a string.")
            self.__check_param_len(description,
                                   msg="Dataset description should be <= {} characters.".format(self.__MAX_DESC_LEN),
                                   length=self.__MAX_DESC_LEN)
        self._desc = description
        self._connection = connection
        self._tables = []
        self._definition = None
        self._session_id = None
        self._folder_id = None
        self.__upload_body = None
        self._dataset_id = dataset_id

        if dataset_id is not None:
            self.__check_param_str(dataset_id, "Dataset ID should be a string.")
            self.__load_definition()

    def add_table(self, name, data_frame, update_policy, to_metric=None, to_attribute=None):
        """Add a Pandas DataFrame to a collection of tables which are later used to update the MicroStrategy dataset.
        Args:
            name (str): Logical name of the table that is visible to users of the dataset in MicroStrategy.
            data_frame (:obj:`pandas.DataFrame`): Pandas DataFrame to add or update.
            update_policy (str): Update operation to perform. One of 'add' (inserts new, unique rows), 'update' (updates
                data in existing rows and columns), 'upsert' (updates existing data and inserts new rows), or 'replace'
                (replaces the existing data with new data).
            to_metric (optional, :obj:`list` of str): By default, Python numeric data types are treated as metrics in
                the MicroStrategy dataset while character and date types are treated as attributes. For example, a
                column of integer-like strings ("1", "2", "3") would, by default, be an attribute in the newly created
                dataset. If the intent is to format this data as a metric, provide the respective column name as
                a string in a list to the `to_metric` parameter.
            to_attribute (optional, :obj:`list` of str): Logical opposite of `to_metric`. Helpful for formatting an
                integer-based row identifier as a primary key in the dataset.
        """

        if not isinstance(data_frame, pd.DataFrame):
            raise TypeError("data_frame must be a valid Pandas DataFrame.")

        if update_policy.lower() not in self.__VALID_POLICY:
            raise ValueError("Update policy must be one of '{}', '{}', '{},' or '{}'.".format(*self.__VALID_POLICY))

        table = {"table_name": name,
                 "data_frame": data_frame,
                 "update_policy": update_policy.lower()}

        # check for duplicate column names when overriding attribute and metric names
        if to_attribute and to_metric and any(col in to_attribute for col in to_metric):
            raise ValueError("Column name(s) present in `to_attribute` also present in 'to_metric'.")

        if to_attribute is not None:
            if any([col for col in to_attribute if col not in data_frame.columns]):
                raise ValueError("Column name(s) in `to_attribute` were not found in `DataFrame.columns`.")
            else:
                table["to_attribute"] = to_attribute

        if to_metric is not None:
            if any([col for col in to_metric if col not in data_frame.columns]):
                raise ValueError("Column name(s) in `to_metric` were not found in `DataFrame.columns`.")
            else:
                table["to_metric"] = to_metric

        self._tables.append(table)

    def create(self, folder_id=None, auto_upload=True, chunksize=100000, progress_bar=True, verbose=False):
        """Creates a new dataset.
        Args:
            folder_id (str, optional): ID of the shared folder that the dataset should be created within. If `None`,
                defaults to the user's My Reports folder.
            auto_upload: If True, automatically uploads the data used to create the dataset definition to the dataset.
                If False, simply creates the dataset but does not upload data to it.
            chunksize (int, optional): Number of rows to transmit to the server with each request when uploading.
            progress_bar(bool, optional): If True (default), show the upload progress bar.
            verbose: If True, prints status information about the dataset upload.
        """

        if folder_id is not None:
            self._folder_id = folder_id
        else:
            self._folder_id = ""

        # generate model of the dataset
        self.__build_model()

        # makes request to create the dataset
        response = datasets.create_multitable_dataset(connection=self._connection, body=self.__model)

        if not response.ok:
            self.__response_handler(response=response, msg="Error creating new dataset model.")
        else:
            response_json = response.json()
            self._dataset_id = response_json['id']

            if verbose:
                print("Created dataset '{}' with ID: '{}'.".format(*[self._name, self._dataset_id]))

        # if desired, automatically upload and publish the data to the new dataset
        if auto_upload:
            self.update(chunksize=chunksize, progress_bar=progress_bar)
            self.publish()

            status = 6  # default initial status
            while status != 1:
                pub = datasets.publish_status(connection=self._connection, dataset_id=self._dataset_id,
                                              session_id=self._session_id)
                if not pub.ok:
                    self.__response_handler(response=pub,
                                            msg="Error publishing the dataset.")
                    break
                else:
                    pub = pub.json()
                    status = pub['status']
                    if status == 1:
                        break

    def update(self, chunksize=100000, progress_bar=True):
        """Updates a dataset with new data.
        Args:
            chunksize (int, optional): Number of rows to transmit to the server with each request.
            progress_bar(bool, optional): If True (default), show the upload progress bar.
        """

        # form request body and create a session for data uploads
        self.__form_upload_body()
        response = datasets.upload_session(connection=self._connection,
                                           dataset_id=self._dataset_id, body=self.__upload_body)

        if not response.ok:
            self.__response_handler(response=response, msg="Error creating new data upload session.")
        else:
            response_json = response.json()
            self._session_id = response_json['uploadSessionId']

            # upload each table
            for ix, _table in enumerate(self._tables):

                _df, _name = _table["data_frame"], _table["table_name"]

                # break the data up into chunks using a generator
                chunks = (_df[i:i + chunksize] for i in range(0, _df.shape[0], chunksize))

                total = _df.shape[0]

                # Count the number of iterations
                it_total = int(total/chunksize) + (total % chunksize != 0)

                pbar = tqdm(chunks, total=it_total, disable=(not progress_bar))
                for index, chunk in enumerate(pbar):
                    if progress_bar:
                        pbar.set_description("Uploading {}/{}".format(ix+1, len(self._tables)))

                    # base64 encode the data
                    encoder = Encoder(data_frame=chunk, dataset_type='multi')
                    b64_enc = encoder.encode

                    # form body of the request
                    body = {"tableName": _name,
                            "index": index + 1,
                            "data": b64_enc}

                    # make request to upload the data
                    response = datasets.upload(connection=self._connection,
                                            dataset_id=self._dataset_id,
                                            session_id=self._session_id,
                                            body=body)

                    if not response.ok:
                        # on error, cancel the previously uploaded data
                        self.__response_handler(response=response, msg="Error uploading data.")
                        datasets.publish_cancel(connection=self._connection,
                                                dataset_id=self._dataset_id,
                                                session_id=self._session_id)

                    if progress_bar:
                        pbar.set_postfix(rows=min((index+1)*chunksize, total))
                pbar.close()
            self._tables = []

    def publish(self):
        """Publish the uploaded data to the selected dataset.
        Returns:
            response: Response from the Intelligence Server acknowledging the publication process.
        """

        response = datasets.publish(connection=self._connection,
                                    dataset_id=self._dataset_id, session_id=self._session_id)

        if not response.ok:
            # on error, cancel the previously uploaded data
            self.__response_handler(response=response, msg="Error publishing uploaded data. Cancelling publication.")
            datasets.publish_cancel(connection=self._connection,
                                    dataset_id=self._dataset_id, session_id=self._session_id)

        return response

    def publish_status(self):
        """Check the status of data that was uploaded to a dataset.
        Returns:
            status: The status of the publication process as a dictionary. In the 'status' key, "1" denotes completion.
        """
        response = datasets.publish_status(connection=self._connection,
                                           dataset_id=self._dataset_id, session_id=self._session_id)
        status = response.json()

        return status

    def delete(self, verbose=False):
        """Delete a dataset that was previously created using the REST API.
         Args:
            verbose: If True, prints status information about the dataset upload.
        """
        response = datasets.delete_dataset(connection=self._connection, dataset_id=self._dataset_id)

        if not response.ok:
            self.__response_handler(response=response,
                                    msg="Error deleting dataset with ID: '{}'".format(self._dataset_id))
        else:
            if verbose:
                print("Successfully deleted dataset ID: '{}'.".format(self._dataset_id))

    def upload_status(self, connection, dataset_id, session_id):
        """Check the status of data that was uploaded to a dataset.
        Args:
            connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
            dataset_id (str): Identifier of a pre-existing dataset.
            session_id (str): Identifer of the server session used for collecting uploaded data.
        """
        response = datasets.publish_status(connection=connection, dataset_id=dataset_id, session_id=session_id)

        self.__response_handler(response=response,
                                msg="Publication status for dataset with ID: '{}':".format(dataset_id))

    def __build_model(self):
        """Create json representation of the dataset."""

        # generate model
        model = Model(tables=self._tables, name=self._name, description=self._desc, folder_id=self._folder_id)
        self.__model = model.get_model()

    def __form_upload_body(self):
        """Form request body for creating an upload session for data uploads"""

        # generate body string
        body = {"tables": [{"name": tbl["table_name"],
                            "updatePolicy": tbl["update_policy"],
                            "columnHeaders": list(tbl["data_frame"].columns)} for tbl in self._tables]}
        self.__upload_body = body

    def __load_definition(self):
        """Load definition of an existing dataset."""

        response = datasets.dataset_definition(connection=self._connection, dataset_id=self._dataset_id)

        if not response.ok:
            self.__response_handler(response=response,
                                    msg="Error loading dataset '{}'. Check dataset ID.".format(self._dataset_id))
        else:
            self._definition = response.json()
            self._name = self._definition['name']
            self._dataset_id = self._definition['id']

    @staticmethod
    def __response_handler(response, msg):
        """Generic error message handler for transactions against datasets.
        Args:
            response: Response object returned by HTTP request.
            msg (str): Message to print in addition to any server-generated error message(s).
        """
        res = json.loads(response.content)
        print(msg)
        print("HTTP %i %s" % (response.status_code, response.reason))
        print("I-Server Error %s, %s" % (res['code'], res['message']))

    @staticmethod
    def __check_param_len(param, msg, length):
        if len(param) >= length:
            raise ValueError(msg)
        else:
            return True

    @staticmethod
    def __check_param_str(param, msg):
        if not isinstance(param, str):
            raise TypeError(msg)
        else:
            return True

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._desc

    @property
    def dataset_id(self):
        return self._dataset_id

    @property
    def upload_body(self):
        return self.__upload_body

    @property
    def session_id(self):
        return self._session_id

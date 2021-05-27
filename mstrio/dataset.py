from typing import Optional
from packaging import version
import pandas as pd
import time
from tqdm.auto import tqdm

from mstrio.api import datasets
import mstrio.config as config
from mstrio.utils.encoder import Encoder
from mstrio.utils.helper import deprecation_warning
import mstrio.utils.helper as helper
from mstrio.utils.model import Model

deprecation_warning("mstrio.dataset", "mstrio.application_objects.datasets.super_cube",
                    "11.3.2.101")


class Dataset:
    """Create and update data in MicroStrategy datasets. Iteratively build a
    dataset with `Dataset.add_table()`. Then, create the dataset using
    `Dataset.create()`. When updating data in the dataset, add individual
    tables to the dataset and define how the dataset should be updated on the
    MicroStrategy server, then call`Dataset.update().` By default
    `Dataset.update()` will upload the data to the Intelligence Server and
    publish the dataset. If you just want to _update_ the dataset but not
    publish the row-level data, use `Dataset.update(auto_publish=False)`
    followed by `Dataset.publish()`.

    Attributes:
        name: Name of the dataset.
        description: Description given to the dataset.
        dataset_id: Unique identifier for the dataset. Used to update a
            pre-existing dataset or generated after creating a new dataset.
        progress_bar(bool, optional): If True (default), show the upload
            progress bar.
        upload_body: Body of the request used to describe the dataset update
            operation.
        session_id: Identifies the data upload session.
    """

    __VALID_POLICY = ['add', 'update', 'replace', 'upsert']
    __MAX_DESC_LEN = 250

    def __init__(self, connection, name=None, description=None, dataset_id=None, progress_bar=True,
                 verbose=True):
        """Interface for creating, updating, and deleting MicroStrategy in-
        memory datasets. When creating a new dataset, provide a dataset name
        and an optional description. When updating a pre-existing dataset,
        provide the dataset identifier. Tables are added to the dataset in an
        iterative manner using `add_table()`.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name (str): Name of the dataset.
            description (str, optional): Description of the dataset. Must be
                less than or equal to 250 characters.
            dataset_id (str, optional): Identifier of a pre-existing dataset.
                Used when updating a pre-existing dataset.
            progress_bar(bool, optional): If True (default), show the upload
                progress bar.
            verbose: Setting to control the amount of feedback from
                the I-Server.
        """
        if name is not None:
            self.__check_param_str(name, msg="Dataset name should be a string.")
            self.__check_param_len(
                name, msg="Dataset name should be <= {} characters.".format(self.__MAX_DESC_LEN),
                max_length=self.__MAX_DESC_LEN)
        self._name = name

        if description is not None:
            self.__check_param_str(description, msg="Dataset description should be a string.")
            self.__check_param_len(
                description,
                msg="Dataset description should be <= {} characters.".format(self.__MAX_DESC_LEN),
                max_length=self.__MAX_DESC_LEN)

        if not connection.application_id:
            helper.exception_handler(
                ("Please provide an application id or application name when creating the"
                 "Connection object."), ConnectionError)
        self._connection = connection
        self._description = description
        self._dataset_id = dataset_id
        self._id = dataset_id
        self.progress_bar = True if progress_bar and config.progress_bar else False
        self._tables = []
        self._definition = None
        self._session_id = None
        self._folder_id = None
        self.__upload_body = None
        self.verbose = verbose

        if dataset_id is not None:
            self.__check_param_str(dataset_id, "Dataset ID should be a string.")
            self.__load_definition()

    def add_table(self, name, data_frame, update_policy, to_metric=None, to_attribute=None):
        """Add a `Pandas.DataFrame` to a collection of tables which are later
        used to populate the MicroStrategy dataset with data.

        Args:
            name (str): Logical name of the table that is visible to users of
                the dataset in MicroStrategy.
            data_frame (:obj:`pandas.DataFrame`): Pandas DataFrame to add or
                update.
            update_policy (str): Update operation to perform. One of 'add'
                (inserts new, unique rows), 'update' (updates data in existing
                rows and columns), 'upsert' (updates existing data and inserts
                new rows), or 'replace' (replaces the existing data with new
                data).
            to_metric (optional, :obj:`list` of str): By default, Python numeric
                data types are treated as metrics in the MicroStrategy dataset
                while character and date types are treated as attributes. For
                example, a column of integer-like strings ("1", "2", "3") would,
                by default, be an attribute in the newly created dataset. If the
                intent is to format this data as a metric, provide the
                respective column name as a string in a list to the `to_metric`
                parameter.
            to_attribute (optional, :obj:`list` of str): Logical opposite of
                `to_metric`. Helpful for formatting an integer-based row
                identifier as a primary key in the dataset.
        """
        update_policy = update_policy.lower()
        version_ok = version.parse(self._connection.iserver_version) >= version.parse("11.2.0300")

        if not isinstance(data_frame, pd.DataFrame):
            raise TypeError("`data_frame` parameter must be a valid `Pandas.DataFrame`.")
        if not helper.check_duplicated_column_names(data_frame):
            raise ValueError(
                "`DataFrame` column names need to be unique for each table in the Dataset.")
        if update_policy not in self.__VALID_POLICY:
            raise ValueError(f"Update policy must be one of {self.__VALID_POLICY}.")
        if self._dataset_id is None and update_policy != "replace" and version_ok:
            raise ValueError(
                "Update policy has to be 'replace' if a dataset is created or overwritten.")
        if to_attribute and to_metric and any(col in to_attribute for col in to_metric):
            raise ValueError(
                "Column name(s) present in `to_attribute` also present in `to_metric`.")

        table = {"table_name": name, "data_frame": data_frame, "update_policy": update_policy}

        if to_attribute is not None:
            if any((col for col in to_attribute if col not in data_frame.columns)):
                raise ValueError(
                    "Column name(s) in `to_attribute` were not found in `DataFrame.columns`.")
            else:
                table["to_attribute"] = to_attribute

        if to_metric is not None:
            if any((col for col in to_metric if col not in data_frame.columns)):
                raise ValueError(
                    "Column name(s) in `to_metric` were not found in `DataFrame.columns`.")
            else:
                table["to_metric"] = to_metric

        self._tables.append(table)

    def create(self, folder_id: Optional[str] = None, auto_upload: bool = True,
               auto_publish: bool = True, chunksize: int = 100000):
        """Creates a new dataset.

        Args:
            folder_id (str, optional): ID of the shared folder that the dataset
                should be created within. If `None`, defaults to the user's
                My Reports folder.
            auto_upload (bool, optional): If True, automatically uploads the
                data to the I-Server. If False, simply creates the dataset
                definition but does not upload data to it.
            auto_publish (bool, optional): If True, automatically publishes the
                data used to create the dataset definition. If False, simply
                creates the dataset but does not publish it. To publish the
                dataset, data has to be uploaded first.
            chunksize (int, optional): Number of rows to transmit to the
                I-Server with each request when uploading.
        """
        if auto_publish and not auto_upload:
            helper.exception_handler(
                "Data needs to be uploaded to the I-Server before the dataset can be published.",
                ValueError)

        if folder_id is not None:
            self._folder_id = folder_id
        else:
            self._folder_id = ""

        # generate model of the dataset
        self.__build_model()

        # makes request to create the dataset
        response = datasets.create_multitable_dataset(connection=self._connection,
                                                      body=self.__model)

        response_json = response.json()
        self._dataset_id = response_json['id']

        if self.verbose:
            print("Created dataset '{}' with ID: '{}'.".format(*[self.name, self._dataset_id]))

        if auto_upload:
            self.update(chunksize=chunksize, auto_publish=auto_publish)

    def update(self, chunksize: int = 100000, auto_publish: bool = True):
        """Updates a dataset with new data.

        Args:
            chunksize (int, optional): Number of rows to transmit to the server
                with each request.
            auto_publish: If True, automatically publishes the data used to
                update the dataset definition to the dataset. If False, simply
                updates the dataset but does not publish it.
        """

        # form request body and create a session for data uploads
        self.__form_upload_body()
        response = datasets.upload_session(connection=self._connection, id=self._dataset_id,
                                           body=self.__upload_body)

        response_json = response.json()
        self._session_id = response_json['uploadSessionId']

        # upload each table
        for ix, _table in enumerate(self._tables):

            _df, _name = _table["data_frame"], _table["table_name"]

            # break the data up into chunks using a generator
            chunks = (_df[i:i + chunksize] for i in range(0, _df.shape[0], chunksize))

            total = _df.shape[0]

            # Count the number of iterations
            it_total = int(total / chunksize) + (total % chunksize != 0)

            pbar = tqdm(chunks, total=it_total, disable=(not self.progress_bar))
            for index, chunk in enumerate(pbar):
                pbar.set_description("Uploading {}/{}".format(ix + 1, len(self._tables)))

                # base64 encode the data
                encoder = Encoder(data_frame=chunk, dataset_type='multi')
                b64_enc = encoder.encode

                # form body of the request
                body = {
                    "tableName": _name,
                    "index": index + 1,
                    "data": b64_enc,
                }

                # make request to upload the data
                response = datasets.upload(
                    connection=self._connection,
                    id=self._dataset_id,
                    session_id=self._session_id,
                    body=body,
                )

                if not response.ok:
                    # on error, cancel the previously uploaded data
                    datasets.publish_cancel(connection=self._connection, id=self._dataset_id,
                                            session_id=self._session_id)

                pbar.set_postfix(rows=min((index + 1) * chunksize, total))
            pbar.close()
        self._tables = []

        # if desired, automatically publish the data to the new dataset
        if auto_publish:
            self.publish()

    def publish(self):
        """Publish the uploaded data to the selected dataset.

        A dataset can be published just once.
        Returns:
            response: Response from the Intelligence Server acknowledging the
                publication process.
        """

        response = datasets.publish(connection=self._connection, id=self._dataset_id,
                                    session_id=self._session_id)

        if not response.ok:
            # on error, cancel the previously uploaded data
            datasets.publish_cancel(connection=self._connection, id=self._dataset_id,
                                    session_id=self._session_id)

        status = 6  # default initial status
        while status != 1:
            status = self.publish_status()['status']
            time.sleep(1)
            if status == 1:
                print("Dataset '%s' published successfully." % self.name)

    def certify(self):
        """Certify the uploaded dataset."""
        response = datasets.toggle_certification(connection=self._connection, id=self._dataset_id)
        if response.ok and self.verbose:
            print("The dataset with ID: '{}' has been certified.".format(self._dataset_id))

    def publish_status(self):
        """Check the status of data that was uploaded to a dataset.

        Returns:
            status: The status of the publication process as a dictionary. In
                the 'status' key, "1" denotes completion.
        """
        response = datasets.publish_status(connection=self._connection, id=self._dataset_id,
                                           session_id=self._session_id)
        status = response.json()

        return status

    def delete(self):
        """Delete a dataset that was previously created using the REST API."""
        datasets.delete_dataset(connection=self._connection, id=self._dataset_id)

        if self.verbose:
            print("Successfully deleted dataset ID: '{}'.".format(self._dataset_id))

    def upload_status(self, connection, dataset_id, session_id):
        """Check the status of data that was uploaded to a dataset.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            dataset_id (str): Identifier of a pre-existing dataset.
            session_id (str): Identifier of the server session used for
                collecting uploaded data.
        """
        response = datasets.publish_status(connection=connection, id=dataset_id,
                                           session_id=session_id)

        helper.response_handler(
            response=response,
            msg="Publication status for dataset with ID: '{}':".format(dataset_id),
            throw_error=False)

    def __build_model(self):
        """Create json representation of the dataset."""

        # generate model
        model = Model(tables=self._tables, name=self.name, description=self.description,
                      folder_id=self._folder_id)
        self.__model = model.get_model()

    def __form_upload_body(self):
        """Form request body for creating an upload session for data
        uploads."""

        # generate body string
        body = {
            "tables": [{
                "name": tbl["table_name"],
                "updatePolicy": tbl["update_policy"],
                "columnHeaders": list(tbl["data_frame"].columns)
            } for tbl in self._tables]
        }
        self.__upload_body = body

    def __load_definition(self):
        """Load definition of an existing dataset."""

        response = datasets.dataset_definition(connection=self._connection, id=self._dataset_id)

        self._definition = response.json()
        self._name = self._definition['name']

    @staticmethod
    def __check_param_len(param, msg, max_length):
        if len(param) > max_length:
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
        return self._description

    @property
    def dataset_id(self):
        helper.deprecation_warning("`dataset_id`", "`id`", "11.3.2.101", module=False)
        return self._dataset_id

    @property
    def upload_body(self):
        return self.__upload_body

    @property
    def session_id(self):
        return self._session_id

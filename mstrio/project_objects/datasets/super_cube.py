import logging
import time
from typing import List, Optional, Union

from packaging import version
import pandas as pd
from tqdm.auto import tqdm

from mstrio import config
from mstrio.api import datasets
from mstrio.connection import Connection
from mstrio.object_management.search_operations import full_search, SearchPattern
from mstrio.utils import helper
from mstrio.utils.encoder import Encoder
from mstrio.utils.entity import CertifyMixin, ObjectSubTypes
from mstrio.utils.model import Model

from .cube import _Cube

logger = logging.getLogger(__name__)


def list_super_cubes(connection: Connection, name_begins: Optional[str] = None,
                     to_dictionary: bool = False, limit: Optional[int] = None,
                     **filters) -> Union[List["SuperCube"], List[dict]]:
    """Get list of SuperCube objects or dicts with them.
    Optionally filter cubes by specifying 'name_begins'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name_begins':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins (string, optional): characters that the cube name must begin
            with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns SuperCube objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']

    Returns:
        list with SuperCubes or list of dictionaries
    """
    connection._validate_project_selected()
    objects_ = full_search(connection, object_types=ObjectSubTypes.SUPER_CUBE,
                           project=connection.project_id, name=name_begins,
                           pattern=SearchPattern.BEGIN_WITH, limit=limit, **filters)
    if to_dictionary:
        return objects_
    else:
        return [SuperCube.from_dict(obj_, connection) for obj_ in objects_]


class SuperCube(_Cube, CertifyMixin):
    """Manage multiple table cube (MTDI aka Super Cube) - according to
    EnumDSSXMLObjectSubTypes its subtype is 779 (DssXmlSubTypeReportEmmaCube).
    It inherits all properties from Cube.

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id: Identifier of a pre-existing cube.
        instance_id (str): Identifier of a cube instance if already initialized,
            None by default.
        name: Name of the SuperCube.
        description: Description given to the SuperCube.
        id: Unique identifier for the super cube. Used to update a
            existing super cube or generated after creating a new super cube.
            (deprecated)
        upload_body (string): upload body of super cube
        session_id (string): ID of session used for uploading and publishing
            super cube
        size(integer): size of cube
        status(integer): status of cube
        path(string): full path of the cube on environment
        owner_id(string): ID of cube's owner
        attributes(list): all attributes of cube
        metrics(list): all metrics of cube
        attr_elements(list): all attributes elements of cube
        selected_attributes(list): IDs of filtered attributes
        selected_metrics(list): IDs of filtered metrics
        selected_attr_elements(list): IDs of filtered attribute elements
        dataframe(object): content of a cube extracted into a
            Pandas `DataFrame`
        table_definition
    """
    _OBJECT_SUBTYPE = ObjectSubTypes.SUPER_CUBE.value
    __VALID_POLICY = ['add', 'update', 'replace', 'upsert']
    __MAX_DESC_LEN = 250
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 name: Optional[str] = None, description: Optional[str] = None,
                 instance_id: Optional[str] = None, progress_bar: bool = True,
                 parallel: bool = True):
        """Initialize super cube.

        When creating new super cube, provide its `name` and an optional
        `description`.
        When updating a pre-existing super cube, provide its `id`. This
        identifier will be then used to initialize super cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str, optional): Identifier of a pre-existing super cube.
                Used when updating a pre-existing super cube.
            name (str): Name of the super cube.
            description (str, optional): Description of the super cube. Must be
                less than or equal to 250 characters.
            instance_id (str): Identifier of an instance if cube instance has
                been already initialized, NULL by default.
            progress_bar(bool, optional): If True (default), show the upload
                progress bar.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
        """
        if name is not None:
            self.__check_param_str(name, msg="Super cube name should be a string.")
            self.__check_param_len(
                name,
                msg=f"Super cube name should be <= {self.__MAX_DESC_LEN} characters.",
                max_length=self.__MAX_DESC_LEN)

        if description is not None:
            self.__check_param_str(description, msg="Super cube description should be a string.")
            self.__check_param_len(
                description, msg="Super cube description should be <= {} characters.".format(
                    self.__MAX_DESC_LEN), max_length=self.__MAX_DESC_LEN)

        connection._validate_project_selected()

        if id is not None:
            super().__init__(connection=connection, id=id, instance_id=instance_id,
                             parallel=parallel, progress_bar=progress_bar)
        else:
            self._init_variables(connection=connection, name=name, description=description,
                                 progress_bar=progress_bar, parallel=parallel)

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        self._tables = []
        self._session_id = None
        self._folder_id = None
        self.__upload_body = None

    def add_table(self, name, data_frame, update_policy, to_metric=None, to_attribute=None):
        """Add a `Pandas.DataFrame` to a collection of tables which are later
        used to populate the MicroStrategy super cube with data.

        Args:
            name (str): Logical name of the table that is visible to users of
                the super cube in MicroStrategy.
            data_frame (:obj:`pandas.DataFrame`): Pandas DataFrame to add or
                update.
            update_policy (str): Update operation to perform. One of 'add'
                (inserts new, unique rows), 'update' (updates data in existing
                rows and columns), 'upsert' (updates existing data and inserts
                new rows), or 'replace' (replaces the existing data with new
                data).
            to_metric (optional, :obj:`list` of str): By default, Python numeric
                data types are treated as metrics while character and date types
                are treated as attributes. For example, a column of integer-like
                strings ("1", "2", "3") would, by default, be an attribute. If
                the intent is to format this data as a metric, provide the
                respective column name as a string in a list to the `to_metric`
                parameter.
            to_attribute (optional, :obj:`list` of str): Logical opposite of
                `to_metric`. Helpful for formatting an integer-based row
                identifier as a primary key in the super cube.
        """
        update_policy = update_policy.lower()
        version_ok = version.parse(self._connection.iserver_version) >= version.parse("11.2.0300")

        if not isinstance(data_frame, pd.DataFrame):
            raise TypeError("`data_frame` parameter must be a valid `Pandas.DataFrame`.")
        if not helper.check_duplicated_column_names(data_frame):
            raise ValueError(
                "`DataFrame` column names need to be unique for each table in the super cube.")
        if update_policy not in self.__VALID_POLICY:
            raise ValueError(f"Update policy must be one of {self.__VALID_POLICY}.")
        if self._id is None and update_policy != "replace" and version_ok:
            raise ValueError(
                "Update policy has to be 'replace' if a super cube is created or overwritten.")
        if to_attribute and to_metric and any(col in to_attribute for col in to_metric):
            raise ValueError(
                "Column name(s) present in `to_attribute` also present in `to_metric`.")

        table = {"table_name": name, "data_frame": data_frame, "update_policy": update_policy}

        if to_attribute is not None:
            if any(col for col in to_attribute if col not in data_frame.columns):
                raise ValueError(
                    "Column name(s) in `to_attribute` were not found in `DataFrame.columns`.")
            else:
                table["to_attribute"] = to_attribute

        if to_metric is not None:
            if any(col for col in to_metric if col not in data_frame.columns):
                raise ValueError(
                    "Column name(s) in `to_metric` were not found in `DataFrame.columns`.")
            else:
                table["to_metric"] = to_metric

        self._tables.append(table)

    def create(self, folder_id: Optional[str] = None, auto_upload: bool = True,
               auto_publish: bool = True, chunksize: int = 100000) -> None:
        """Create a new super cube and initialize cube object after successful
        creation. This function does not return new super cube, but it updates
        object inplace.

        Args:
            folder_id (str, optional): ID of the shared folder in which the
                super cube will be created. If `None`, defaults to the user's
                My Reports folder.
            auto_upload (bool, optional): If True, automatically uploads the
                data to the I-Server. If False, simply creates the super cube
                definition but does not upload data to it.
            auto_publish (bool, optional): If True, automatically publishes the
                data used to create the super cube definition. If False, simply
                creates the super cube but does not publish it. To publish the
                super cube, data has to be uploaded first.
            chunksize (int, optional): Number of rows to transmit to the
                I-Server with each request when uploading.
        """
        if auto_publish and not auto_upload:
            raise ValueError(
                "Data needs to be uploaded to the I-Server before the super cube can be published."
            )

        if folder_id is not None:
            self._folder_id = folder_id
        else:
            self._folder_id = ""

        # generate model of the super cube
        self.__build_model()

        # makes request to create the super cube
        response = datasets.create_multitable_dataset(connection=self._connection,
                                                      body=self.__model)
        self._set_object_attributes(**response.json())

        if config.verbose:
            logger.info("Created super cube '{}' with ID: '{}'.".format(*[self.name, self._id]))

        if auto_upload:
            self.update(chunksize=chunksize, auto_publish=auto_publish)

        # after creating super cube fetch definition and create filter object
        self._get_definition()

    def update(self, chunksize: int = 100000, auto_publish: bool = True):
        """Updates a super cube with new data.

        Args:
            chunksize (int, optional): Number of rows to transmit to the server
                with each request.
            auto_publish: If True, automatically publishes the data used to
                update the super cube definition to the super cube. If False,
                simply updates the super cube but does not publish it.
        """

        # form request body and create a session for data uploads
        self.__form_upload_body()
        response = datasets.upload_session(connection=self._connection, id=self._id,
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

            pbar = tqdm(chunks, total=it_total, disable=(not self._progress_bar))
            for index, chunk in enumerate(pbar):
                pbar.set_description(f"Uploading {ix + 1}/{len(self._tables)}")

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
                    id=self._id,
                    session_id=self._session_id,
                    body=body,
                )

                if not response.ok:
                    # on error, cancel the previously uploaded data
                    datasets.publish_cancel(connection=self._connection, id=self._id,
                                            session_id=self._session_id)

                pbar.set_postfix(rows=min((index + 1) * chunksize, total))
            pbar.close()
        self._tables = []

        # if desired, automatically publish the data to the new super cube
        if auto_publish:
            self.publish()

    def save_as(self, name: str, description: Optional[str] = None,
                folder_id: Optional[str] = None, table_name: Optional[str] = None) -> "SuperCube":
        """Creates a new single-table cube with the data frame stored in the
        SuperCube instance `SuperCube.dataframe`.

        Args:
            name(str): Name of cube.
            description(str): Description of the cube.
            folder_id (str, optional): ID of the shared folder that the super
                cube should be created within. If `None`, defaults to the user's
                My Reports folder.
            table_name (str, optional): Name of the table. If None (default),
                the first table name of the original cube will be used.
        """
        if len(self._table_names) > 1:
            helper.exception_handler(msg="""This feature works only for the single-table cubes.
                                            \rTo export multi-table cube use `create` method.""")
        elif self._dataframe is None:
            raise ValueError(
                "Current cube has to be fetched with `to_dataframe` method first to create a copy."
            )
        else:
            if table_name is None:
                table_name = self._table_names[0]["name"]
            new_cube = SuperCube(self._connection, name=name, description=description)
            new_cube.add_table(name=table_name, data_frame=self.dataframe, update_policy="replace")
            new_cube.create(folder_id=folder_id)
            return new_cube

    def publish(self) -> bool:
        """Publish the uploaded data to the selected super cube.

        Note:
            A super cube can be published just once.

        Returns:
            True if the data was published successfully, else False.
        """

        response = datasets.publish(connection=self._connection, id=self._id,
                                    session_id=self._session_id)

        if not response.ok:
            # on error, cancel the previously uploaded data
            datasets.publish_cancel(connection=self._connection, id=self._id,
                                    session_id=self._session_id)
            return False

        status = 6  # default initial status
        while status != 1:
            status = self.publish_status()['status']
            time.sleep(1)
            if status == 1:
                # clear instance_id to force new instance creation
                self.instance_id = None
                if config.verbose:
                    logger.info(f"Super cube '{self.name}' published successfully.")
                return True

    def publish_status(self):
        """Check the status of data that was uploaded to a super cube.

        Returns:
            status: The status of the publication process as a dictionary. In
                the 'status' key, "1" denotes completion.
        """
        if not self._session_id:
            raise AttributeError("No upload session created.")
        else:
            response = datasets.publish_status(connection=self._connection, id=self._id,
                                               session_id=self._session_id)
            return response.json()

    def upload_status(self, connection: Connection, id: str, session_id: str):
        """Check the status of data that was uploaded to a super cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing super cube.
            session_id (str): Identifier of the server session used for
                collecting uploaded data.
        """
        # TODO not sure why we have this functionality twice
        response = datasets.publish_status(connection=connection, id=id, session_id=session_id)

        helper.response_handler(response=response,
                                msg=f"Publication status for super cube with ID: '{id}':",
                                throw_error=False)

    def __build_model(self):
        """Create json representation of the super cube."""

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
    def upload_body(self):
        return self.__upload_body

    @property
    def session_id(self) -> str:
        return self._session_id

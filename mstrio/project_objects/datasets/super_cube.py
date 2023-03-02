import logging
import time
from typing import Optional

import pandas as pd
from tqdm.auto import tqdm

from mstrio import config
from mstrio.api import cubes, datasets
from mstrio.connection import Connection
from mstrio.object_management import Folder, get_predefined_folder_contents, PredefinedFolders
from mstrio.object_management.search_operations import full_search, SearchPattern
from mstrio.utils import helper
from mstrio.utils.encoder import Encoder
from mstrio.utils.entity import CertifyMixin, ObjectSubTypes
from mstrio.utils.model import Model
from mstrio.utils.version_helper import is_server_min_version
from .cube import _Cube

logger = logging.getLogger(__name__)


def list_super_cubes(
    connection: Connection,
    name: Optional[str] = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters,
) -> list["SuperCube"] | list[dict]:
    """Get list of SuperCube objects or dicts with them.
    Optionally filter cubes by specifying 'name'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name = ?onny will return Sonny and Tonny

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): value the search pattern is set to, which
            will be applied to the names of super cubes being searched
        search_pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Contains. Possible values are available
            in ENUM mstrio.object_management.SearchPattern.
            Default value is BEGIN WITH (4).
        project_id (string, optional): Project ID
        project_name (string, optional): Project name
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
    project_id = helper.get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects_ = full_search(
        connection,
        object_types=ObjectSubTypes.SUPER_CUBE,
        project=project_id,
        name=name,
        pattern=search_pattern,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects_
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

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instance_id: Optional[str] = None,
        progress_bar: bool = True,
        parallel: bool = True
    ):
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
                max_length=self.__MAX_DESC_LEN
            )

        if description is not None:
            self.__check_param_str(description, msg="Super cube description should be a string.")
            self.__check_param_len(
                description,
                msg="Super cube description should be <= {} characters.".format(
                    self.__MAX_DESC_LEN
                ),
                max_length=self.__MAX_DESC_LEN
            )

        connection._validate_project_selected()

        if id is not None:
            super().__init__(
                connection=connection,
                id=id,
                instance_id=instance_id,
                parallel=parallel,
                progress_bar=progress_bar
            )
        else:
            self._init_variables(
                connection=connection,
                name=name,
                description=description,
                progress_bar=progress_bar,
                parallel=parallel
            )

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        self._tables = []
        self._session_id = None
        # used to check publish status after completing publish
        self.__last_session_id = None
        self._folder_id = None
        self.__upload_body = None
        # used to store indexes for every table after an update to have correct
        # index in case of doing multiple updates without publish
        self.__update_indexes = {}

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

        if not isinstance(data_frame, pd.DataFrame):
            raise TypeError("`data_frame` parameter must be a valid `Pandas.DataFrame`.")
        if not helper.check_duplicated_column_names(data_frame):
            raise ValueError(
                "`DataFrame` column names need to be unique for each table in the super cube."
            )
        self.__check_update_policy(update_policy)
        if to_attribute and to_metric and any(col in to_attribute for col in to_metric):
            raise ValueError(
                "Column name(s) present in `to_attribute` also present in `to_metric`."
            )

        table = {"table_name": name, "data_frame": data_frame, "update_policy": update_policy}

        if to_attribute is not None:
            if any(col for col in to_attribute if col not in data_frame.columns):
                raise ValueError(
                    "Column name(s) in `to_attribute` were not found in `DataFrame.columns`."
                )
            else:
                table["to_attribute"] = to_attribute

        if to_metric is not None:
            if any(col for col in to_metric if col not in data_frame.columns):
                raise ValueError(
                    "Column name(s) in `to_metric` were not found in `DataFrame.columns`."
                )
            else:
                table["to_metric"] = to_metric

        self._tables.append(table)
        if not self.__update_indexes.get(name):
            self.__update_indexes[name] = 0

    def __check_update_policy(self, update_policy: str) -> None:
        if update_policy not in self.__VALID_POLICY:
            raise ValueError(f"Update policy must be one of {self.__VALID_POLICY}.")

    def remove_table(self, name):
        """Removes a table from a collection of tables which are
        later used to populate the MicroStrategy super cube with data.

        Note: this operation is executed locally and is used only to prepare
            data before sending it to server. You can check current state of
            tables with property `tables`.

        Args:
            name (str): Logical name of the table that is visible to users of
                the super cube in MicroStrategy.
        """
        self._tables = [t for t in self._tables if t.get('table_name') != name]

    def __check_folder_contents(self, name: str, folder_id: Optional[str] = None):
        """Check if folder already have object with given name.
        If folder_id is None, check My Reports folder.
        """

        if folder_id:
            folder = Folder(self.connection, id=folder_id)
            contents = folder.get_contents(name=name)
        else:
            contents = get_predefined_folder_contents(
                self.connection, PredefinedFolders.PROFILE_REPORTS, name=name
            )

        if contents:
            raise ValueError(
                f"Super Cube with name {self.name} already exist in {folder_id or 'My Reports'} "
                "folder. If you want to override already existing cube, add tables with "
                "update policy `replace` and call 'create()' method with argument 'force=True'."
            )

    def __are_all_tables_with_replace_policy(self):
        return all(table['update_policy'] == 'replace' for table in self.tables)

    def create(
        self,
        folder_id: Optional[str] = None,
        auto_upload: bool = True,
        auto_publish: bool = True,
        chunksize: int = 100000,
        force: bool = False
    ) -> None:
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
            force (bool, optional): If True, skip checking if a super cube
                already exist in the folder with the given name.
                Defaults to False.
        """
        if auto_publish and not auto_upload:
            raise ValueError(
                "Data needs to be uploaded to the I-Server before the super cube can be published."
            )

        if folder_id is not None:
            self._folder_id = folder_id
        else:
            self._folder_id = ""

        if not force:
            self.__check_folder_contents(self.name, folder_id)

        if (
            force
            and is_server_min_version(self.connection, '11.2.0300')
            and not self.__are_all_tables_with_replace_policy()
        ):
            raise ValueError(
                "All the tables must be added with update policy 'replace', when trying to "
                "override existing Super Cube with 'force=True'."
            )

        # generate model of the super cube
        self.__build_model()

        # makes request to create the super cube
        response = datasets.create_multitable_dataset(
            connection=self._connection, body=self.__model
        )
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

        if not self._session_id:
            response = datasets.upload_session(
                connection=self._connection, id=self._id, body=self.__upload_body
            )
            response_json = response.json()
            self._session_id = response_json['uploadSessionId']
            self.__last_session_id = None

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
                    "index": self.__update_indexes.get(_name, 0) + index + 1,
                    "data": b64_enc,
                }

                # make request to upload the data
                response = datasets.upload(
                    connection=self._connection,
                    id=self._id,
                    session_id=self._session_id,
                    body=body,
                    throw_error=False
                )

                if not response.ok:
                    # on error, cancel the previously uploaded data
                    datasets.publish_cancel(
                        connection=self._connection, id=self._id, session_id=self._session_id
                    )
                    self.reset_session()
                    pbar.close()
                    return

                pbar.set_postfix(rows=min((index + 1) * chunksize, total))
            pbar.close()

            # prepare index in case of the next update operation for this table
            # without publishing
            self.__update_indexes[_name] += it_total
        self._tables = []

        # if desired, automatically publish the data to the new super cube
        if auto_publish:
            self.publish()

    def save_as(
        self,
        name: str,
        description: Optional[str] = None,
        folder_id: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> "SuperCube":
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
            helper.exception_handler(
                msg="""This feature works only for the single-table cubes.
                                            \rTo export multi-table cube use `create` method."""
            )
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
        response = datasets.publish(
            connection=self._connection, id=self._id, session_id=self._session_id
        )

        if not response.ok:
            # on error, cancel the previously uploaded data
            datasets.publish_cancel(
                connection=self._connection, id=self._id, session_id=self._session_id
            )
            self.reset_session()
            return False

        status = 6  # default initial status
        while status != 1:
            status = self.publish_status()['status']
            time.sleep(1)
            if status == 1:
                # clear instance_id to force new instance creation
                self.instance_id = None
                self.reset_session()
                if config.verbose:
                    logger.info(f"Super cube '{self.name}' published successfully.")
                return True

    def publish_status(self):
        """Check the status of data that was uploaded to a super cube.

        Returns: status: The status of the publication process as a dictionary.
            In the 'status' key, "1" denotes completion.
        """
        # after publish, `self._session_id` is reset to force new session
        # creation in the next update, so we have to use its value saved in
        # `self.__last_session_id`
        session_id = self._session_id if self._session_id else self.__last_session_id

        return self.upload_status(connection=self.connection, id=self.id, session_id=session_id)

    def reset_session(self):
        """Reset upload session."""
        if self._session_id:
            # save last session id in case of checking status of publish
            self.__last_session_id = self._session_id
            # clear session_id to force new session creation
            self._session_id = None
            self.__update_indexes = {}

    def export_sql_view(self) -> str:
        """Export SQL View of a Super Cube.

        Returns:
            SQL View of a Super Cube.
        """
        res = cubes.get_sql_view(self._connection, self._id)
        sql_statement = res.json()['sqlStatement']
        return sql_statement

    def __build_model(self):
        """Create json representation of the super cube."""

        # generate model
        model = Model(
            tables=self._tables,
            name=self.name,
            description=self.description,
            folder_id=self._folder_id
        )
        self.__model = model.get_model()

    def __form_upload_body(self):
        """Form request body for creating an upload session for data
        uploads."""

        # generate body string
        body = {
            "tables": [
                {
                    "name": tbl["table_name"],
                    "updatePolicy": tbl["update_policy"],
                    "columnHeaders": list(tbl["data_frame"].columns)
                } for tbl in self._tables
            ]
        }
        self.__upload_body = body

    @staticmethod
    def upload_status(connection: Connection, id: str, session_id: str):
        """Check the status of data that was uploaded to a super cube.

        Args:
            connection (Optional[Connection]): MicroStrategy connection object
                returned by `connection.Connection()`.
            id (Optional[str]): Identifier of a pre-existing super cube.
            session_id (Optional[str]): Identifier of the server session used
                for collecting uploaded data.

        Returns:
            status: The status of the publication process as a dictionary. In
                the 'status' key, "1" denotes completion.
        """
        if not session_id:
            raise AttributeError("No upload session created.")
        else:
            response = datasets.publish_status(connection=connection, id=id, session_id=session_id)
            return response.json()

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

    @property
    def tables(self):
        return self._tables

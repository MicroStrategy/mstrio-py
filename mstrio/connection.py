import contextlib
import inspect
import logging
import os
from base64 import b64encode
from datetime import datetime
from enum import IntEnum
from functools import partial
from getpass import getpass
from typing import TYPE_CHECKING

import requests
from requests import (  # NOQA F401 (imports for ease of access)
    ConnectTimeout,
    ReadTimeout,
    Session,
    Timeout,
)
from requests.adapters import HTTPAdapter, Retry
from requests.cookies import RequestsCookieJar

from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.resolvers import get_project_id_from_params_set

if TYPE_CHECKING:
    from urllib3 import disable_warnings
    from urllib3.exceptions import InsecureRequestWarning

    from mstrio.project_objects.applications import Application
    from mstrio.server.project import Project
else:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    from requests.packages.urllib3 import disable_warnings

from mstrio import config
from mstrio.api import authentication, hooks, misc
from mstrio.helpers import IServerError, IServerException, VersionException
from mstrio.utils import helper, sessions

logger = logging.getLogger(__name__)

APPLICATION_TYPE_PYTHON = 76
APPLICATION_TYPE_WEB = 35

try:
    # assigned right away instead of being calculated in a method so that
    # if a user creates their own `workstationData` variable, this will still
    # show false as this is run before the script is executed in most cases
    _is_in_workstation: bool | None = any(
        'workstationData' in dict(inspect.getmembers(frame[0]))['f_globals']
        for frame in inspect.stack()
    )
except Exception:
    # This is not essential enough info to try to handle it
    # in a more sophisticated way
    _is_in_workstation = None


_validate_or_none = partial(helper.validate_param_value, special_values=[None])


class LoginMode(IntEnum):
    STANDARD = 1
    ANONYMOUS = 8
    LDAP = 16
    API_TOKEN = 4096


def get_connection(
    workstation_data: dict,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    ssl_verify: bool = False,
    verbose: bool = True,
    request_timeout: int | float | None = None,
    request_retry_on_timeout_count: int | None = None,
) -> 'Connection | None':
    """Connect to environment without providing user's credentials.

    It is possible to provide `project`, `project_id` or `project_name` to
    select project. When all are `None`, project selection is cleared.
    Project can be also selected later by calling method
    `select_project` on Connection object.

    Note:
        `ssl_verify` is set to False by default just for the `get_connection`
        function as it is designed for usage inside Workstation.
        When `ssl_verify` is set to False, warning about missing certificate
        verification (InsecureRequestWarning) is disabled.

    Args:
        workstation_data (object): object which is stored in a 'workstationData'
            variable within Workstation
        project (Project, str, optional): Project object or ID or name
            of the project to be selected
        project_id (str, optional): ID of project to be selected
        project_name (str, optional): Name of project to be selected
        ssl_verify (bool, optional): If False (default), does not verify the
            server's SSL certificates
        verbose (bool, optional): True by default. Controls the amount of
            feedback from the I-Server logged by mstrio-py (logger level INFO
            if `True`, WARNING if `False`).
        request_timeout (int | float, optional): Time (in seconds) after
            which every request aborts waiting for response and raises
            `requests.Timeout`. Defaults to `None`, meaning no timeout.
            If set to `None`, fallbacks to
            `mstrio.config.default_request_timeout` value, if set.
        request_retry_on_timeout_count (int, optional): Number of times
            to retry a request in case of a timeout. If `None` or less
            than 2, no retries will be attempted.

    Returns:
        connection to I-Server or None in case of some error
    """
    if not ssl_verify:
        disable_warnings(category=InsecureRequestWarning)

    try:
        logger.info('Creating connection from Workstation Data object...')
        # get base url from Workstation Data object
        base_url = helper.url_check(workstation_data['defaultEnvironment']['url'])
        # get headers from Workstation Data object
        headers = workstation_data['defaultEnvironment']['headers']
        # get cookies from Workstation Data object
        cookies = workstation_data['defaultEnvironment']['cookies']

        # prepare cookies for request
        jar = RequestsCookieJar()
        for c in cookies:
            cookie_values = {'domain': '', 'path': '/'}
            cookie_values.update(c)
            jar.set(
                cookie_values['name'],
                cookie_values['value'],
                domain=cookie_values['domain'],
                path=cookie_values['path'],
            )
    except Exception as e:
        logger.error(
            f'Some error occurred while preparing data to get identity token: \n{e}'
        )
        return None

    # get identity token
    response = requests.post(
        base_url + '/api/auth/identityToken',
        headers=headers,
        cookies=jar,
        verify=ssl_verify,
    )
    if response.ok:
        # create connection to I-Server
        conn = Connection(
            base_url,
            identity_token=response.headers['X-MSTR-IdentityToken'],
            project=project,
            project_id=project_id,
            project_name=project_name,
            ssl_verify=ssl_verify,
            verbose=verbose,
            request_timeout=request_timeout,
            request_retry_on_timeout_count=request_retry_on_timeout_count,
        )
        conn._through_get_connection = True
        return conn

    logger.error(
        f'HTTP {response.status_code} - {response.reason}, Message {response.text}'
    )

    return None


class Connection:
    """Connect to and interact with the Strategy One environment.

    Creates a connection object which is used in subsequent requests and
    manages the user's connection with the Strategy One REST and Intelligence
    Servers.
    The connection is automatically renewed, or reconnected if server's session
    associated with the connection expires due to inactivity.

    Examples:
        >>> from mstrio import connection
        >>>
        >>> # connect to the environment and chosen project
        >>> conn = connection.Connection(
        >>>     base_url="https://demo.microstrategy.com/MicroStrategyLibrary",
        >>>     username="username",
        >>>     password="password",
        >>>     project_name="MicroStrategy Tutorial"
        >>> )
        >>> # disconnect
        >>> conn.close()

    Attributes:
        base_url: URL of the Strategy One REST API server.
        username: Username.
        project_id: Id of the connected Strategy One Project.
        project_name: Name of the connected Strategy One Project.
        login_mode: Authentication mode. Standard = 1 (default), LDAP = 16
            or API Token = 4096.
        ssl_verify: If True (default), verifies the server's SSL certificates
            with each request.
        user_id: Id of the authenticated user
        user_full_name: Full name of the authenticated user
        user_initials: Initials of the authenticated user
        iserver_version: Version of the I-Server
        web_version: Version of the Web Server
        token: authentication token
        working_set: Number of report/document instances that are kept in memory
            on the server before the oldest instance is replaced.
        max_search: Maximum number of concurrent searches.
        timeout: time after the server's session expires, in seconds
        request_timeout: time (in seconds) after which every request aborts
            waiting for response and raises `requests.Timeout`. If not
            provided explicitly, defaults to
            `mstrio.config.default_request_timeout` parameter value.
    """

    def __init__(
        self,
        base_url: str,
        username: str | None = None,
        password: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        login_mode: int | LoginMode | None = None,
        ssl_verify: bool = True,
        certificate_path: str | None = None,
        proxies: dict | None = None,
        identity_token: str | None = None,
        api_token: str | None = None,
        application_id: 'str | Application | None' = None,
        working_set: int | None = None,
        max_search: int | None = None,
        verbose: bool = True,
        request_timeout: int | float | None = None,
        request_retry_on_timeout_count: int | None = None,
    ):
        """Establish a connection with Strategy One REST API.

        You can establish connection by either providing set of values
        (`username`, `password`, `login_mode`), just `identity_token`
        or just `api_token`.

        When `api_token` is provided and `login_mode` is set to 4096
        or omitted, the connection is established using API Token and
        all other authentication parameters are ignored.

        Note:
            When project cannot be established or is not provided, it is reset
            to `None`.

        Args:
            base_url (str): URL of the Strategy One REST API server.
                Typically of the form:
                "https://<mstr_env>.com/MicroStrategyLibrary/api"
            username (str, optional): Username
            password (str, optional): Password
            project_name (str, optional): Name of the project you intend
                to connect to (case-sensitive). Provide either Project ID
                or Project Name.
            project_id (str, optional): Id of the project you intend to
                connect to (case-sensitive). Provide either Project ID
                or Project Name.
            login_mode (int | LoginMode, optional): Specifies the
                authentication mode to use. Supported authentication
                modes are: Standard (1) (default), LDAP (16), or
                API Token (4096). Defaults to 1 unless `api_token` is
                provided, then 4096.
            ssl_verify (bool, optional): If True (default), verifies the
                server's SSL certificates with each request
            certificate_path (str, optional): Path to SSL certificate file, if
                None and ssl_verify is True then the certificate will be looked
                for in current working directory
            proxies (dict, optional): Dictionary mapping protocol or protocol
                and host to the URL of the proxy (e.g. {'http': 'foo.bar:3128',
                'http://host.name': 'foo.bar:4012'})
            identity_token (str, optional): Identity token for delegated
                session. Used for connection initialized by GUI.
            api_token (str, optional): API token for authenticating using
                `login_mode` 4096. For other login modes it is ignored.
            application_id (str, Application, optional): Log in using the
                login mode configured in a custom application. If it's
                not provided, the server login modes are used.
            working_set (int, optional): Number of report/document instances
                that are kept in memory on the server before the oldest instance
                is replaced. Minimum value is 3, if None, will be set to 10 by
                default.
            max_search (int, optional): Maximum number of concurrent searches.
                If None, will be set to 3 by default.
            verbose (bool, optional): True by default. Controls the amount of
                feedback from the I-Server logged by mstrio-py (logger level
                INFO if `True`, WARNING if `False`).
            request_timeout (int | float, optional): Time (in seconds) after
                which every request aborts waiting for response and raises
                `requests.Timeout`. Defaults to `None`, meaning no timeout.
                If set to `None`, fallbacks to
                `mstrio.config.default_request_timeout` value, if set.
            request_retry_on_timeout_count (int, optional): Number of times
                to retry a request in case of a timeout. If `None` or less
                than 1, no retries will be attempted.
        """

        if login_mode is None:
            login_mode = 4096 if api_token else 1

        login_mode = get_enum_val(login_mode, LoginMode)

        if max_search is not None:
            helper.validate_param_value('max_search', max_search, int)

        _validate_or_none('working_set', working_set, int, min_val=3)

        # set the verbosity globally
        config.verbose = bool(verbose and config.verbose)

        self.base_url = helper.url_check(base_url)
        self.username = username
        self.login_mode = login_mode
        self.certificate_path = certificate_path
        self.identity_token = identity_token
        self.api_token = api_token
        self._session = self.__configure_session(ssl_verify, certificate_path, proxies)
        self._web_version = None
        self._iserver_version = None
        self._user_id = None
        self._user_full_name = None
        self._user_initials = None
        self.__password = password
        self.last_active = None
        self.timeout = None
        self.working_set = working_set
        self.max_search = max_search
        self.__through_get_connection: bool = False
        self._request_timeout = None
        self.set_request_timeout(request_timeout)
        self._request_retry_on_timeout_count = None
        self.set_request_retry_on_timeout_count(request_retry_on_timeout_count)

        # do not check application type if delegated
        self._application_type = (
            APPLICATION_TYPE_PYTHON if identity_token is None else None
        )

        from mstrio.project_objects.applications import Application

        self.application_id = (
            application_id.id
            if isinstance(application_id, Application)
            else application_id
        )

        # delegate identity token or connect and create new session
        if self.identity_token:
            self.delegate()
        else:
            self.connect()

        if not self.__check_version():
            msg = (
                f'This version of mstrio is only supported on MicroStrategy 11.1.0400 '
                f'or higher.\n'
                f'Current Intelligence Server version: {self._iserver_version}\n'
                f'Current MicroStrategy Web version: {self._web_version}'
            )
            logger.warning(msg)
            helper.exception_handler(
                msg='MicroStrategy Version not supported.',
                exception_type=VersionException,
            )
            return

        from mstrio.utils.version_helper import is_server_min_version

        # In some versions APPLICATION_TYPE_PYTHON is supported at login,
        # but several features are not available. Reconnect with
        # APPLICATION_TYPE_WEB if the server version is not compatible
        if (
            self._application_type
            and self._application_type != APPLICATION_TYPE_WEB
            and not is_server_min_version(self, '11.5.0600')
        ):
            self._application_type = APPLICATION_TYPE_WEB
            self.token = None
            self.connect()

        if application_id and not is_server_min_version(self, '11.3.1200'):
            logger.warning(
                "The `application_id` argument requires iServer version 11.3.1200 "
                f"or later. Since your server version: {self._iserver_version} "
                "is not compatible, this parameter will be omitted."
            )
            self.application_id = None

        self.project_id = None
        self.select_project(project, project_id, project_name)

    @property
    def _through_get_connection(self) -> bool:
        """Indicates if the connection was established via `get_connection`."""
        return self.__through_get_connection

    @_through_get_connection.setter
    def _through_get_connection(self, value: bool) -> None:
        if value is True and not self.is_run_in_workstation():
            raise SyntaxError(
                "Connection established via `get_connection` can only be used "
                "inside Workstation."
            )
        self.__through_get_connection = value

    def __enter__(self):
        if self._through_get_connection:
            raise SyntaxError(
                "Connection established via `get_connection` cannot be used "
                "as a context manager (aka. using `with` syntax) as running "
                "the script would disconnect you from Workstation."
            )
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def connect(self) -> None:
        """Authenticates the user and creates a new connection with the
        Intelligence Server.

        If an active connection is detected, the session is renewed.
        """
        response = self._renew() if self.token else None

        if response and response.ok:
            self._reset_timeout()
            if config.verbose:
                logger.info(
                    'Connection to Strategy One Intelligence Server was renewed.'
                )
        else:
            response = self._login()
            self._reset_timeout()
            self.token = response.headers['X-MSTR-AuthToken']
            self._fetch_session_info()

            if config.verbose:
                logger.info(
                    'Connection to Strategy One Intelligence Server has been '
                    'established.'
                )

    renew = connect
    open = connect

    def delegate(self):
        """Delegates identity token to get authentication token and connect to
        Strategy One Intelligence Server."""
        response = authentication.delegate(
            self, self.identity_token, whitelist=[('ERR003', 401)]
        )
        if response.ok:
            self._reset_timeout()
            self.token = response.headers['X-MSTR-AuthToken']
            self._fetch_session_info()
            if config.verbose:
                logger.info(
                    'Connection with Strategy One Intelligence Server has been '
                    'delegated.'
                )
        else:
            logger.warning(
                "Could not share existing connection session, please input credentials:"
            )
            self.__prompt_credentials()
            self.connect()

    def get_identity_token(self) -> str:
        """Create new identity token using existing authentication token."""
        response = authentication.identity_token(self)
        return response.headers['X-MSTR-IdentityToken']

    def get_api_token(self) -> str:
        """Create new API token using existing authentication token."""
        response = authentication.api_token(self)
        return response.json()['apiToken']

    def validate_identity_token(self) -> bool:
        """Validate the identity token."""
        validate = authentication.validate_identity_token(self, self.identity_token)
        return validate.ok

    def close(self):
        """Closes a connection with Strategy One REST API."""
        if self._through_get_connection:
            raise SyntaxError(
                "Connection established via `get_connection` cannot be closed "
                "as it would disconnect you from Workstation."
            )

        authentication.logout(connection=self, whitelist=[('ERR009', 401)])
        self._session.close()
        self.token = None

        if config.verbose:
            logger.info(
                'Connection to Strategy One Intelligence Server has been closed.'
            )

    disconnect = close

    def status(self) -> bool:
        """Checks if the session is still alive.

        Raises:
            HTTPError if I-Server behaves unexpectedly
        """
        status = self._status()

        if status.status_code == 200:
            logger.info('Connection to Strategy One Intelligence Server is active.')
            return True
        else:
            logger.info('Connection to Strategy One Intelligence Server is not active.')
            return False

    def select_project(
        self,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Select project for the given connection based.

        Args:
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Raises:
            ValueError: if project with given id or name does not exist or
                cannot find a unique project with given name
        """

        proj_id = get_project_id_from_params_set(
            self,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        if self.project_id == proj_id:
            return

        if not proj_id:
            self.project_id = None
            self._session.headers['X-MSTR-ProjectID'] = None

            if config.verbose:
                logger.info('No Project selected in Connection object.')

            return None

        if config.verbose:
            from mstrio.server.project import Project

            logger.info('Project selected in Connection object:')
            Project(self, id=proj_id)  # this will log the project info

        self.project_id = proj_id
        self._session.headers['X-MSTR-ProjectID'] = self.project_id

    @contextlib.contextmanager
    def temporary_project_change(
        self,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Context manager for temporary changing the selected project.

        Note:
            This just changes the project assigned to this `Connection`
            instance temporarily. Designed to be called using `with` statement.
            See `Examples` below for usage.

        Args:
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Examples:
            >>> from mstrio import Connection
            >>>
            >>> # initially we select project "MicroStrategy Tutorial"
            >>> conn = Connection(..., project="MicroStrategy Tutorial")
            >>> # ... some actions on the `conn` ...
            >>>
            >>> with conn.temporary_project_change(project=None):
            >>>     # ... inside this block no project is selected ...
            >>>
            >>> # ... outside the `with` block again ...
            >>> # ... "MicroStrategy Tutorial" is selected ...
        """
        orig_project_id = self.project_id
        self.select_project(
            project=project, project_id=project_id, project_name=project_name
        )
        try:
            yield self  # grabbing this yield is not necessary but may be useful
        finally:
            if self and getattr(self, 'select_project', None):  # some edge-case-cover
                self.select_project(project=orig_project_id)

    def set_request_timeout(self, timeout: int | float | None) -> None:
        """Set the request timeout time for this connection's requests.

        Args:
            timeout (int | float | None): Time (in seconds) after which every
                request made by this connection will be aborted if
                not completed. If set to `None`, fallbacks to
                `mstrio.config.default_request_timeout` value, if set.
        """
        _validate_or_none('timeout', timeout, [float, int], min_val=0.001)
        self._request_timeout = timeout

    def set_request_retry_on_timeout_count(self, count: int | None) -> None:
        """Set the number of times to retry a request in case of a timeout.

        Args:
            count (int | None): Number of times to retry a request in case of
                a timeout. If `None` or less than 1, no retries will be
                attempted.
        """
        _validate_or_none('count', count, int, min_val=0)
        self._request_retry_on_timeout_count = count

    @sessions.log_request(logger)
    @sessions.renew_session
    def _request(
        self, method_name: str, url: str, endpoint: str, **kwargs
    ) -> requests.Response:
        if url and endpoint:
            raise ValueError(
                'Either `url` or `endpoint` argument should be provided, not both.'
            )

        if endpoint:
            url = self.base_url + endpoint

        name2method = {
            'GET': self._session.get,
            'POST': self._session.post,
            'PUT': self._session.put,
            'PATCH': self._session.patch,
            'DELETE': self._session.delete,
            'HEAD': self._session.head,
        }
        method = name2method[method_name.upper()]
        kwargs = {"timeout": self.request_timeout, **kwargs}

        retry_count = self._request_retry_on_timeout_count
        retries_left = retry_count + 1 if retry_count else 1

        while retries_left > 0:
            try:
                return method(url, **kwargs)
            except Timeout as err:
                retries_left -= 1
                if not retries_left:
                    if retry_count:
                        raise err.__class__(
                            f"Retrying request {retry_count} times failed. "
                            "See traceback for more details."
                        ) from err
                    raise err

    def get(self, url=None, *, endpoint=None, **kwargs):
        """Sends a GET request."""
        return self._request('GET', url, endpoint, **kwargs)

    def post(self, url=None, *, endpoint=None, **kwargs):
        """Sends a POST request."""
        return self._request('POST', url, endpoint, **kwargs)

    def put(self, url=None, *, endpoint=None, **kwargs):
        """Sends a PUT request."""
        return self._request('PUT', url, endpoint, **kwargs)

    def patch(self, url=None, *, endpoint=None, **kwargs):
        """Sends a PATCH request."""
        return self._request('PATCH', url, endpoint, **kwargs)

    def delete(self, url=None, *, endpoint=None, **kwargs):
        """Sends a DELETE request."""
        return self._request('DELETE', url, endpoint, **kwargs)

    def head(self, url=None, *, endpoint=None, **kwargs):
        """Sends a HEAD request."""
        return self._request('HEAD', url, endpoint, **kwargs)

    def _status(self):
        return authentication.session_status(connection=self)

    def _login(self):
        try:
            return authentication.login(connection=self)
        except IServerError as e:
            if 'constraint violations' in str(e):
                # The error indicates APPLICATION_TYPE_PYTHON is not supported
                logger.error(
                    'Server does not support new Python Application Type '
                    f'({APPLICATION_TYPE_PYTHON}). Retrying connection with old '
                    f'setup: WEB Application Type ({APPLICATION_TYPE_WEB}).'
                )

                self._application_type = APPLICATION_TYPE_WEB
                return authentication.login(connection=self)
            else:
                raise e

    def _renew(self):
        return authentication.session_renew(connection=self)

    def _renew_or_reconnect(self):
        response = self._renew() if self.token else None

        if not self.identity_token and (not response or not response.ok):
            response = self._login()
            self.token = response.headers['X-MSTR-AuthToken']

        if response and response.ok:
            self._reset_timeout()

    def _fetch_session_info(self):
        res = self._status()
        json_data = res.json() if res.ok else {}
        self.timeout = json_data.get('timeout')
        self.working_set = json_data.get('workingSet')
        self.max_search = json_data.get('maxSearch')

    def _reset_timeout(self):
        self.last_active = datetime.now()

    def _is_session_expired(self):
        return (datetime.now() - self.last_active).seconds > self.timeout

    def _get_authorization(self) -> str:
        self.__prompt_credentials()
        credentials = f"{self.username}:{self.__password}".encode()
        encoded_credential = b64encode(credentials)
        auth = "Basic " + str(encoded_credential, 'utf-8')
        return auth

    def _validate_project_selected(self) -> None:
        if self.project_id is None:
            raise AttributeError(
                "Project not selected. Select project using `select_project` method."
            )

    def __prompt_credentials(self) -> None:
        self.username = self.username or input("Username: ")
        self.__password = self.__password or getpass("Password: ")
        self.login_mode = self.login_mode or int(
            input("Login mode (1 - Standard, 16 - LDAP): ")
        )

    def __check_version(self) -> bool:
        """Checks version of I-Server and Strategy One Web and store these
        variables."""

        resp = misc.server_status(self)
        if not resp:
            logger.warning(
                "Could not read status of I-Server. "
                "Assuming misconfiguration of Library and "
                "Server Version of 11.1.0400 or higher. "
                "Some functionalities may not work properly. "
                "Please check configuration of Library and I-Server availability."
            )
            return True

        err_msg = (
            "I-Server is currently unavailable or connection creation failed. "
            "Please verify or contact your administrator."
        )

        if not resp.ok:
            raise IServerException(err_msg)

        json_response = resp.json()
        if (
            not json_response
            or "iServerVersion" not in json_response
            or "webVersion" not in json_response
        ):
            raise IServerException(err_msg)

        self._iserver_version = json_response["iServerVersion"][:9]
        self._web_version = json_response["webVersion"][:9]

        from mstrio.utils.version_helper import meets_minimal_version

        ret = meets_minimal_version(self._iserver_version, "11.1.0400")

        if ret and self._iserver_version:
            # save the version of IServer in config file
            config.iserver_version = self._iserver_version

        return ret

    def __configure_session(
        self,
        verify,
        certificate_path,
        proxies,
        existing_session=None,
        retries=2,
        backoff_factor=0.3,
    ):
        """Creates a shared requests.Session() object with configuration from
        the initialization. Additional parameters change how the HTTPAdapter is
        configured.

        Args:
            existing_session (requests.Session() object, optional): Optional
                existing Session object to configure
            retries (int, optional): number of retries for certain type of
                requests (i.e. get)
            backoff_factor (float, optional):  backoff factor to apply between
                attempts after the second try (most errors are resolved
                immediately by a second try without a delay). urllib3 will sleep
                for: {backoff factor} * (2 ^ ({number of total retries} - 1))
                seconds. If the backoff_factor is 0.1, then sleep() will sleep
                for [0.0s, 0.2s, 0.4s, ...] between retries. It will never be
                longer than Retry. BACKOFF_MAX. By default, backoff is disabled
                (set to 0).
        """
        session = existing_session or Session()
        session.proxies = proxies or {}
        session.verify = self._configure_ssl(verify, certificate_path)

        response_hooks = []
        if config.debug:
            response_hooks.append(hooks.print_url)
        if config.save_responses:
            response_hooks.append(hooks.save_response)
        if response_hooks:
            session.hooks['response'] = response_hooks

        status_forcelist = frozenset([413, 429, 500, 503])  # retry after status

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    @staticmethod
    def _configure_ssl(ssl_verify, certificate_path):
        def get_certs_from_cwd():
            cert_extensions = ['crt', 'pem', 'p12']
            return [
                file
                for file in os.listdir('.')
                if file.split('.')[-1] in cert_extensions
            ]

        def find_cert_in_cwd(ssl_verify):
            certs = get_certs_from_cwd()
            if certs and ssl_verify:
                return certs[0]
            else:
                return ssl_verify

        if certificate_path:
            return certificate_path
        return find_cert_in_cwd(ssl_verify)

    def __get_user_info(self) -> None:
        response = authentication.get_info_for_authenticated_user(
            connection=self
        ).json()
        self._user_id = response.get("id")
        self._user_full_name = response.get("fullName")
        self._user_initials = response.get("initials")

    @classmethod
    def is_run_in_workstation(cls) -> bool | None:
        """Check if the script is run in Workstation.

        Returns:
            bool: True if the script is run in Workstation, False otherwise.
                It may return None when gathering this info failed.
        """
        return _is_in_workstation

    @property
    def project_name(self) -> str | None:
        if self.project_id is None:
            return None

        from mstrio.server.project import Project

        with config.temp_verbose_disable():
            return Project(self, id=self.project_id).name

    @property
    def user_id(self) -> str:
        if not self._user_id:
            self.__get_user_info()
        return self._user_id

    @property
    def user_full_name(self) -> str:
        if not self._user_full_name:
            self.__get_user_info()
        return self._user_full_name

    @property
    def user_initials(self) -> str:
        if not self._user_initials:
            self.__get_user_info()
        return self._user_initials

    @property
    def web_version(self) -> str | None:
        if not self._web_version:
            self.__check_version()

        return self._web_version

    @property
    def iserver_version(self) -> str | None:
        if not self._iserver_version:
            self.__check_version()

        return self._iserver_version

    @property
    def request_timeout(self) -> int | float | None:
        if self._request_timeout is not None:
            return self._request_timeout
        return config.default_request_timeout

    @property
    def request_retry_on_timeout_count(self) -> int | None:
        return self._request_retry_on_timeout_count

    @property
    def token(self) -> str:
        return self._session.headers.get('X-MSTR-AuthToken')

    @token.setter
    def token(self, token: str) -> str:
        self._session.headers['X-MSTR-AuthToken'] = token
        return token

    @property
    def headers(self):
        return self._session.headers

    @property
    def environment(self):
        from mstrio.server.environment import Environment

        return Environment(connection=self)

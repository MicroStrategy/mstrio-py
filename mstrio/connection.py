from base64 import b64encode
from datetime import datetime
from getpass import getpass
import logging
import os
from typing import Optional

from packaging import version
import requests
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests.cookies import RequestsCookieJar
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from mstrio import config
from mstrio.api import authentication, exceptions, hooks, misc, projects
from mstrio.utils import helper, sessions

logger = logging.getLogger(__name__)


def get_connection(
    workstation_data: dict,
    project_name: Optional[str] = None,
    project_id: Optional[str] = None,
    ssl_verify: bool = False
) -> Optional["Connection"]:
    """Connect to environment without providing user's credentials.

    It is possible to provide `project_id` or `project_name` to select
    project. When both `project_id` and `project_name` are `None`,
    project selection is cleared. When both `project_id` and
    `project_name` are provided, `project_name` is ignored.
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
        project_name (str, optional): name of project (aka project)
            to select
        project_id (str, optional): id of project (aka project)
            to select
        ssl_verify (bool, optional): If False (default), does not verify the
            server's SSL certificates

    Returns:
        connection to I-Server or None is case of some error
    """
    if not ssl_verify:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    try:
        logger.info('Creating connection from Workstation Data object...')
        # get base url from Workstation Data object
        base_url = workstation_data['defaultEnvironment']['url']
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
                path=cookie_values['path']
            )
    except Exception as e:
        logger.error(f'Some error occurred while preparing data to get identity token: \n{e}')
        return None

    # get identity token
    r = requests.post(
        base_url + 'api/auth/identityToken', headers=headers, cookies=jar, verify=ssl_verify
    )
    if r.ok:
        # create connection to I-Server
        return Connection(
            base_url,
            identity_token=r.headers['X-MSTR-IdentityToken'],
            project_id=project_id,
            project_name=project_name,
            ssl_verify=ssl_verify
        )
    else:
        logger.error(f'HTTP {r.status_code} - {r.reason}, Message {r.text}')
        return None


class Connection:
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and
    manages the user's connection with the MicroStrategy REST and Intelligence
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
        base_url: URL of the MicroStrategy REST API server.
        username: Username.
        project_name: Name of the connected MicroStrategy Project.
        project_id: Id of the connected MicroStrategy Project.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates
            with each request.
        user_id: Id of the authenticated user
        user_full_name: Full name of the authenticated user
        user_initials: Initials of the authenticated user
        iserver_version: Version of the I-Server
        web_version: Version of the Web Server
        token: authentication token
        timeout: time after the server's session expires, in seconds
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        project_name: Optional[str] = None,
        project_id: Optional[str] = None,
        login_mode: int = 1,
        ssl_verify: bool = True,
        certificate_path: Optional[str] = None,
        proxies: Optional[dict] = None,
        identity_token: Optional[str] = None,
        verbose: bool = True
    ):
        """Establish a connection with MicroStrategy REST API.

        You can establish connection by either providing set of values
        (`username`, `password`, `login_mode`) or just `identity_token`.

        When both `project_id` and `project_name` are `None`,
        project selection is cleared. When both `project_id`
        and `project_name` are provided, `project_name` is ignored.

        Args:
            base_url (str): URL of the MicroStrategy REST API server.
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
            login_mode (int, optional): Specifies the authentication mode to
                use. Supported authentication modes are: Standard (1)
                (default) or LDAP (16)
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
            verbose (bool, optional): True by default. Controls the amount of
                feedback from the I-Server.
        """

        # set the verbosity globally
        config.verbose = True if verbose and config.verbose else False
        self.base_url = helper.url_check(base_url)
        self.username = username
        self.login_mode = login_mode
        self.certificate_path = certificate_path
        self.identity_token = identity_token
        self._session = self.__configure_session(ssl_verify, certificate_path, proxies)
        self._web_version = None
        self._iserver_version = None
        self._user_id = None
        self._user_full_name = None
        self._user_initials = None
        self.__password = password
        self.last_active = None
        self.timeout = None

        if self.__check_version():
            # save the version of IServer in config file
            config.iserver_version = self.iserver_version
            # delegate identity token or connect and create new session

            if self.identity_token:
                self.delegate()
            else:
                self.connect()

            self.select_project(project_id, project_name)
        else:
            msg = (
                f'This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.\n'
                f'Current Intelligence Server version: {self.iserver_version}\n'
                f'Current MicroStrategy Web version: {self.web_version}'
            )
            logger.warning(msg)
            helper.exception_handler(
                msg='MicroStrategy Version not supported.',
                exception_type=exceptions.VersionException
            )

    def __enter__(self):
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
                logger.info('Connection to MicroStrategy Intelligence Server was renewed.')
        else:
            response = self._login()
            self._reset_timeout()
            self.token = response.headers['X-MSTR-AuthToken']
            self.timeout = self._get_session_timeout()

            if config.verbose:
                logger.info(
                    'Connection to MicroStrategy Intelligence Server has been established.'
                )

    renew = connect

    def delegate(self):
        """Delegates identity token to get authentication token and connect to
        MicroStrategy Intelligence Server."""
        response = authentication.delegate(self, self.identity_token, whitelist=[('ERR003', 401)])
        if response.ok:
            self._reset_timeout()
            self.token = response.headers['X-MSTR-AuthToken']
            self.timeout = self._get_session_timeout()
            if config.verbose:
                logger.info(
                    'Connection with MicroStrategy Intelligence Server has been delegated.'
                )
        else:
            print("Could not share existing connection session, please input credentials:")
            self.__prompt_credentials()
            self.connect()

    def get_identity_token(self) -> str:
        """Create new identity token using existing authentication token."""
        response = authentication.identity_token(self)
        return response.headers['X-MSTR-IdentityToken']

    def validate_identity_token(self) -> bool:
        """Validate the identity token."""
        validate = authentication.validate_identity_token(self, self.identity_token)
        return validate.ok

    def close(self):
        """Closes a connection with MicroStrategy REST API."""
        authentication.logout(connection=self, whitelist=[('ERR009', 401)])

        self._session.close()

        self.token = None

        if config.verbose:
            logger.info('Connection to MicroStrategy Intelligence Server has been closed.')

    def status(self) -> bool:
        """Checks if the session is still alive.

        Raises:
            HTTPError if I-Server behaves unexpectedly
        """
        status = self._status()

        if status.status_code == 200:
            logger.info('Connection to MicroStrategy Intelligence Server is active.')
            return True
        else:
            logger.info('Connection to MicroStrategy Intelligence Server is not active.')
            return False

    def select_project(
        self, project_id: Optional[str] = None, project_name: Optional[str] = None
    ) -> None:
        """Select project for the given connection based on project_id or
        project_name.

        When both `project_id` and `project_name` are `None`, project selection
        is cleared. When both `project_id` and `project_name` are provided,
        `project_name` is ignored.

        Args:
            project_id: id of project to select
            project_name: name of project to select

        Raises:
            ValueError: if project with given id or name does not exist
        """
        if project_id is None and project_name is None:
            self.project_id = None
            self.project_name = None
            if config.verbose:
                logger.info('No project selected.')
            return None

        if project_id and project_name:
            tmp_msg = (
                'Both `project_id` and `project_name` arguments provided. '
                'Selecting project based on `project_id`.'
            )
            helper.exception_handler(msg=tmp_msg, exception_type=Warning)

        _projects = projects.get_projects(connection=self).json()
        if project_id:
            # Find which project name matches the project ID provided
            tmp_projects = helper.filter_list_of_dicts(_projects, id=project_id)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = (
                    f"Error connecting to project with id: {project_id}. "
                    "Project with given id does not exist or user has no access."
                )
                raise ValueError(tmp_msg)
        elif project_name:
            # Find which project ID matches the project name provided
            tmp_projects = helper.filter_list_of_dicts(_projects, name=project_name)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = (
                    f"Error connecting to project with name: {project_name}. "
                    "Project with given name does not exist or user has no access."
                )
                raise ValueError(tmp_msg)

        self.project_id = tmp_projects[0]['id']
        self.project_name = tmp_projects[0]['name']
        self._session.headers['X-MSTR-ProjectID'] = self.project_id

    @sessions.log_request(logger)
    @sessions.renew_session
    def get(self, url, **kwargs):
        return self._session.get(url, **kwargs)

    @sessions.log_request(logger)
    @sessions.renew_session
    def post(self, url, **kwargs):
        return self._session.post(url, **kwargs)

    @sessions.log_request(logger)
    @sessions.renew_session
    def put(self, url, **kwargs):
        return self._session.put(url, **kwargs)

    @sessions.log_request(logger)
    @sessions.renew_session
    def patch(self, url, **kwargs):
        return self._session.patch(url, **kwargs)

    @sessions.log_request(logger)
    @sessions.renew_session
    def delete(self, url, **kwargs):
        return self._session.delete(url, **kwargs)

    @sessions.log_request(logger)
    @sessions.renew_session
    def head(self, url, **kwargs):
        return self._session.head(url, **kwargs)

    def _status(self):
        return authentication.session_status(connection=self)

    def _login(self):
        return authentication.login(connection=self)

    def _renew(self):
        return authentication.session_renew(connection=self)

    def _renew_or_reconnect(self):
        response = self._renew() if self.token else None

        if not self.identity_token and (not response or not response.ok):
            response = self._login()
            self.token = response.headers['X-MSTR-AuthToken']

        if response.ok:
            self._reset_timeout()

    def _get_session_timeout(self):
        res = self._status()
        return res.json()['timeout'] if res.ok else None

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
        self.login_mode = self.login_mode or input("Login mode (1 - Standard, 16 - LDAP): ")

    def __check_version(self) -> bool:
        """Checks version of I-Server and MicroStrategy Web and store these
        variables."""

        def get_server_status():
            json_response = misc.server_status(self).json()
            try:
                iserver_version = json_response["iServerVersion"][:9]
            except KeyError:
                raise exceptions.IServerException(
                    "I-Server is currently unavailable. Please contact your administrator."
                )
            web_version = json_response.get("webVersion")
            web_version = web_version[:9] if web_version else None
            return iserver_version, web_version

        self._iserver_version, self._web_version = get_server_status()
        return version.parse(self.iserver_version) >= version.parse("11.1.0400")

    def __configure_session(
        self,
        verify,
        certificate_path,
        proxies,
        existing_session=None,
        retries=2,
        backoff_factor=0.3
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
            return [file for file in os.listdir('.') if file.split('.')[-1] in cert_extensions]

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
        response = authentication.get_info_for_authenticated_user(connection=self).json()
        self._user_id = response.get("id")
        self._user_full_name = response.get("fullName")
        self._user_initials = response.get("initials")

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
    def web_version(self) -> str:
        return self._web_version

    @property
    def iserver_version(self) -> str:
        return self._iserver_version

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

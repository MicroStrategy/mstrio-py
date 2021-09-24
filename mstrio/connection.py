from base64 import b64encode
from getpass import getpass
import os
from typing import Optional, Union

from packaging import version
import requests
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests.cookies import RequestsCookieJar

from mstrio import config
from mstrio.api import authentication, exceptions, hooks, misc, projects
from mstrio.utils.helper import deprecation_warning
import mstrio.utils.helper as helper


def get_connection(workstation_data: dict, project_name: str = None, project_id: str = None,
                   application_name: str = None,
                   application_id: str = None) -> Union["Connection", None]:
    """Connect to environment without providing user's credentials.

    It is possible to provide `project_id` or `project_name` to select
    project. When both `project_id` and `project_name` are `None`,
    project selection is cleared. When both `project_id` and
    `project_name` are provided, `project_name` is ignored.
    Project can be also selected later by calling method
    `select_project` on Connection object.
    Args:
        workstation_data (object): object which is stored in a 'workstationData'
            variable within Workstation
        project_name (str, optional): name of project (aka project)
            to select
        project_id (str, optional): id of project (aka project)
            to select
        application_name(str, optional): deprecated. Use project_name instead.
        application_id(str, optional): deprecated. Use project_id instead.
    Returns:
        connection to I-Server or None is case of some error
    """
    if (application_name or application_id):
        helper.deprecation_warning(
            '`application_name` and `application_id`',
            '`project_name` and `project_id`',
            '11.3.4.101',  # NOSONAR
            False)
        project_name = project_name or application_name
        project_id = project_id or application_id

    try:
        print('Creating connection from Workstation Data object...', flush=True)
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
            jar.set(cookie_values['name'], cookie_values['value'], domain=cookie_values['domain'],
                    path=cookie_values['path'])
    except Exception as e:
        print('Some error occurred while preparing data to get identity token:')
        print(e)
        return None

    # get identity token
    r = requests.post(base_url + 'api/auth/identityToken', headers=headers, cookies=jar)
    if r.ok:
        # create connection to I-Server
        return Connection(base_url, identity_token=r.headers['X-MSTR-IdentityToken'],
                          project_id=project_id, project_name=project_name)
    else:
        print('HTTP %i - %s, Message %s' % (r.status_code, r.reason, r.text), flush=True)
        return None


class Connection():
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and
    manages the user's connection with the MicroStrategy REST and Intelligence
    Servers.

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
        project_name: Name of the connected MicroStrategy Applicaiton.
        project_id: Id of the connected MicroStrategy Applicaiton.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates
            with each request.
        user_id: Id of the authenticated user
        user_full_name: Full name of the authenticated user
        user_initials: Initials of the authenticated user
        iserver_version: Version of the I-Server
        web_version: Version of the Web Server
    """

    def __init__(self, base_url: str, username: Optional[str] = None,
                 password: Optional[str] = None, project_name: Optional[str] = None,
                 project_id: Optional[str] = None, login_mode: int = 1, ssl_verify: bool = True,
                 certificate_path: Optional[str] = None, proxies: Optional[dict] = None,
                 identity_token: Optional[str] = None, verbose: bool = True,
                 application_name: Optional[str] = None, application_id: Optional[str] = None):
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
            application_name (str, optional): deprecated. Use project_name
            instead.
            application_id (str, optional): deprecated. Use project_id instead.
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
        if (application_id or application_name):
            deprecation_warning(
                "`application_id` and `application_name`",
                "`project_id` or `project_name`",
                "11.3.4.101",  # NOSONAR
                False)

        # set the verbosity globally
        config.verbose = True if verbose and config.verbose else False
        self.base_url = helper.url_check(base_url)
        self.username = username
        self.login_mode = login_mode
        self.certificate_path = certificate_path
        self.identity_token = identity_token
        self.session = self.__configure_session(ssl_verify, certificate_path, proxies)
        self._web_version = None
        self._iserver_version = None
        self._user_id = None
        self._user_full_name = None
        self._user_initials = None
        self.__password = password
        project_id = project_id or application_id
        project_name = project_name or application_name

        if self.__check_version():
            # save the version of IServer in config file
            config.iserver_version = self.iserver_version
            # delegate identity token or connect and create new sesssion
            self.delegate() if self.identity_token else self.connect()
            self.select_project(project_id, project_name)
        else:
            print("""This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.
                     \rCurrent Intelligence Server version: {}
                     \rCurrent MicroStrategy Web version: {}
                     """.format(self.iserver_version, self.web_version))
            helper.exception_handler(msg="MicroStrategy Version not supported.",
                                     exception_type=exceptions.VersionException)

    def connect(self) -> None:
        """Authenticates the user and creates a new connection with the
        Intelligence Server.

        If an active connection is detected, the session is renewed.
        """
        response = authentication.session_renew(connection=self)
        if not response.ok:
            response = authentication.login(connection=self)
            self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
            if config.verbose:
                print("Connection to MicroStrategy Intelligence Server has been established.")
        else:
            if config.verbose:
                print("Connection to MicroStrategy Intelligence Server was renewed.")

    def delegate(self) -> None:
        """Delegates identity token to get authentication token and connect to
        MicroStrategy Intelligence Server."""
        response = authentication.delegate(self, self.identity_token, whitelist=[('ERR003', 401)])
        if response.ok:
            self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
            if config.verbose:
                print("Connection with MicroStrategy Intelligence Server has been delegated.")
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

    def close(self) -> None:
        """Closes a connection with MicroStrategy REST API."""
        authentication.logout(connection=self)
        self.session.close()

        if config.verbose:
            print("Connection to MicroStrategy Intelligence Server has been closed")

    def renew(self) -> None:
        """Checks if the session is still alive.

        If so, renews the session and extends session expiration.
        """
        status = authentication.session_renew(connection=self)

        if status.status_code == 204:
            if config.verbose:
                print("Your connection to MicroStrategy Intelligence Server was renewed.")
        else:
            response = authentication.login(connection=self)
            self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
            if config.verbose:
                print("""Connection with MicroStrategy Intelligence Server was not active.
                         \rNew connection has been established.""")

    def status(self) -> bool:
        """Checks if the session is still alive.

        Raises:
            HTTPError if I-Server behaves unexpectedly
        """
        status = authentication.session_status(connection=self)

        if status.status_code == 200:
            print("Connection to MicroStrategy Intelligence Server is active.")
            return True
        else:
            print("Connection to MicroStrategy Intelligence Server is not active.")
            return False

    def select_project(self, project_id: Optional[str] = None,
                       project_name: Optional[str] = None) -> None:
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
                print("No project selected.")
            return None

        if project_id is not None and project_name is not None:
            tmp_msg = ("Both `project_id` and `project_name` arguments provided. "
                       "Selecting project based on `project_id`.")
            helper.exception_handler(msg=tmp_msg, exception_type=Warning)

        _projects = projects.get_projects(connection=self).json()
        if project_id is not None:
            # Find which project name matches the project ID provided
            tmp_projects = helper.filter_list_of_dicts(_projects, id=project_id)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = (f"Error connecting to project with id: {project_id}. "
                           "Project with given id does not exist or user has no access.")
                raise ValueError(tmp_msg)
        elif project_name is not None:
            # Find which project ID matches the project name provided
            tmp_projects = helper.filter_list_of_dicts(_projects, name=project_name)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = (f"Error connecting to project with name: {project_name}. "
                           "Project with given name does not exist or user has no access.")
                raise ValueError(tmp_msg)

        self.project_id = tmp_projects[0]['id']
        self.project_name = tmp_projects[0]['name']
        self.session.headers['X-MSTR-ProjectID'] = self.project_id

    def select_application(self, application_id: Optional[str] = None,
                           application_name: Optional[str] = None) -> None:
        deprecation_warning(
            "`select_application` method",
            "`select_project` method",
            "11.3.4.101",  # NOSONAR
            False)
        self.select_project(project_id=application_id, project_name=application_name)

    def _get_authorization(self) -> str:
        self.__prompt_credentials()
        credentials = "{}:{}".format(self.username, self.__password).encode('utf-8')
        encoded_credential = b64encode(credentials)
        auth = "Basic " + str(encoded_credential, 'utf-8')
        return auth

    def _validate_project_selected(self) -> None:
        if self.project_id is None:
            raise AttributeError(
                "Project not selected. Select project using `select_project` method.")

    def __prompt_credentials(self) -> None:
        self.username = self.username if self.username is not None else input("Username: ")
        self.__password = self.__password if self.__password is not None else getpass("Password: ")
        self.login_mode = self.login_mode if self.login_mode else input(
            "Login mode (1 - Standard, 16 - LDAP): ")

    def __check_version(self) -> bool:
        """Checks version of I-Server and MicroStrategy Web and store these
        variables."""

        def get_server_status():
            json_response = misc.server_status(self).json()
            try:
                iserver_version = json_response["iServerVersion"][:9]
            except KeyError:
                raise exceptions.IServerException(
                    "I-Server is currently unavailable. Please contact your administrator.")
            web_version = json_response.get("webVersion")
            web_version = web_version[:9] if web_version else None
            return iserver_version, web_version

        self._iserver_version, self._web_version = get_server_status()
        return version.parse(self.iserver_version) >= version.parse("11.1.0400")

    def __configure_session(self, verify, certificate_path, proxies, existing_session=None,
                            retries=2, backoff_factor=0.3):
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
        session.proxies = proxies if proxies is not None else {}
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

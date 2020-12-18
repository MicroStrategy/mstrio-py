import os
from getpass import getpass
from packaging import version
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from base64 import b64encode

from mstrio.api import authentication, misc, projects, exceptions
import mstrio.utils.helper as helper
from requests import Session
import mstrio.config as config


class Connection(object):
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and
    manages the user's connection with the MicroStrategy REST and Intelligence
    Servers.

    Example:
        # import
        from mstrio import connection

        # connect to the environment and chosen project
        conn = connection.Connection(
            base_url="https://demo.microstrategy.com/MicroStrategyLibrary/api",
            username="username",
            password="password",
            project_name="MicroStrategy Tutorial"
        )
        # disconnect
        conn.close()

    Attributes:
        base_url: URL of the MicroStrategy REST API server.
        username: Username.
        password: Password.
        project_name: Name of the connected MicroStrategy Project.
        project_id: Id of the connected MicroStrategy Project.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates
            with each request.
    """
    __VRCH = "11.1.0400"
    __DEFAULT_METHOD_WHITELIST = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])
    __RETRY_AFTER_STATUS_CODES = frozenset([413, 429, 500, 503])

    def __init__(self, base_url=None, username=None, password=None, project_name=None, project_id=None, login_mode=1,
                 ssl_verify=True, certificate_path=None, proxies=None, identity_token=None, verbose=True):
        """Establish a connection with MicroStrategy REST API.

        Args:
            base_url (str, optional): URL of the MicroStrategy REST API server.
                Typically of the form:
                    "https://<mstr_env>.com/MicroStrategyLibrary/api"
            username (str, optional): Username
            password (str, optional): Password
            project_name (str, optional): Name of the project you intend to
                connect to.Case-sensitive. You should provide either Project ID
                or Project Name.
            project_id (str, optional): Id of the project you intend to connect
                to. Case-sensitive. You should provide either Project ID
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

        config.verbose = True if verbose and config.verbose else False    # set the verbosity globally
        self.base_url = helper.url_check(base_url)
        self.username = username
        self.password = password
        self.login_mode = login_mode
        self.web_version = None
        self.iserver_version = None
        self.certificate_path = certificate_path
        self.identity_token = identity_token
        self.session = self.__configure_session(ssl_verify, certificate_path, proxies)

        if self.__check_version():
            # save the version of IServer in config file
            config.iserver_version = self.iserver_version
            # delegate identity token or connect and create new sesssion
            self.delegate() if self.identity_token else self.connect()
            self.select_project(project_id=project_id, project_name=project_name)
        else:
            print("""This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.
                     \rCurrent Intelligence Server version: {}
                     \rCurrent MicroStrategy Web version: {}
                     """.format(self.iserver_version, self.web_version))
            helper.exception_handler(msg="MicroStrategy Version not supported.",
                                     exception_type=exceptions.VersionException)
        self.user_id = self.__get_user_info()['id']

    def connect(self):
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

    def delegate(self):
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

    def get_identity_token(self):
        """Create new identity token using existing authentication token."""
        response = authentication.identity_token(self)
        return response.headers['X-MSTR-IdentityToken']

    def validate_identity_token(self, token):
        """Validate the identity token."""
        validate = authentication.validate_identity_token(self, self.identity_token)
        return validate.ok

    def close(self):
        """Closes a connection with MicroStrategy REST API."""
        authentication.logout(connection=self)
        self.session.close()

        if config.verbose:
            print("Connection to MicroStrategy Intelligence Server has been closed")

    def renew(self):
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

    def status(self):
        """Checks if the session is still alive."""
        status = authentication.session_status(connection=self)

        if status.status_code == 200:
            print("Connection to MicroStrategy Intelligence Server is active.")
        else:
            print("Connection to MicroStrategy Intelligence Server is not active.")

    def select_project(self, project_id: str = None, project_name: str = None) -> None:
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
            return

        if project_id is not None and project_name is not None:
            tmp_msg = "Both project_id and project_name arguments provided. Selecting project based on project_id."
            helper.exception_handler(msg=tmp_msg, exception_type=Warning, throw_error=False)

        _projects = projects.get_projects(connection=self).json()
        if project_id is not None:
            # Find which project name matches the project ID provided
            tmp_projects = helper.filter_list_of_dicts(_projects, id=project_id)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = "Error connecting to project with id: {}. Project with given id does not exist or user has no access.".format(project_id)
                raise ValueError(tmp_msg)
        elif project_name is not None:
            # Find which project ID matches the project name provided
            tmp_projects = helper.filter_list_of_dicts(_projects, name=project_name)
            if not tmp_projects:
                self.project_id, self.project_name = None, None
                tmp_msg = "Error connecting to project with name: {}. Project with given name does not exist or user has no access.".format(project_name)
                raise ValueError(tmp_msg)

        self.project_id = tmp_projects[0]['id']
        self.project_name = tmp_projects[0]['name']
        self.session.headers['X-MSTR-ProjectID'] = self.project_id

    def _get_authorization(self):
        self.__prompt_credentials()
        credentials = "{}:{}".format(self.username, self.password).encode('utf-8')
        encoded_credential = b64encode(credentials)
        auth = "Basic " + str(encoded_credential, 'utf-8')
        return auth

    def _validate_project_selected(self):
        if self.project_id is None:
            raise AttributeError("Project not selected. Select project using `connection.select_project()`.")

    def __prompt_credentials(self):
        self.username = self.username if self.username is not None else input("Username: ")
        self.password = self.password if self.password is not None else getpass("Password: ")
        self.login_mode = self.login_mode if self.login_mode else input("Login mode (1 - Standard, 16 - LDAP): ")

    def __check_version(self):
        """Checks version of I-Server and MicroStrategy Web."""
        json_response = misc.server_status(self).json()
        try:
            self.iserver_version = json_response["iServerVersion"][:9]
        except KeyError:
            raise exceptions.IServerException("I-Server is currently unavailable. Please contact your administrator.")
        self.web_version = json_response.get("webVersion")
        self.web_version = self.web_version[:9] if self.web_version else None
        iserver_version_ok = version.parse(self.iserver_version) >= version.parse(self.__VRCH)

        return iserver_version_ok

    def __configure_session(self, verify, certificate_path, proxies, existing_session=None, retries=2,
                            backoff_factor=0.3, status_forcelist=None, method_whitelist=None):
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
            status_forcelist: list of http statuses that will be retried
        """
        session = existing_session or Session()
        session.proxies = proxies if proxies is not None else {}
        session.verify = self._configure_ssl(verify, certificate_path)

        hooks = []
        if config.debug:
            hooks.append(helper.print_url)
        if config.save_responses:
            hooks.append(helper.save_response)
        if hooks:
            session.hooks['response'] = hooks

        if status_forcelist is None:
            status_forcelist = self.__RETRY_AFTER_STATUS_CODES
        if method_whitelist is None:
            method_whitelist = self.__DEFAULT_METHOD_WHITELIST

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            method_whitelist=method_whitelist,
            raise_on_status=False
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

    def __get_user_info(self):
        response = authentication.get_info_for_authenticated_user(connection=self)
        return response.json()

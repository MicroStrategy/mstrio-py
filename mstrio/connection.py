from base64 import b64encode
from getpass import getpass
import os

from packaging import version
from requests import Session
from requests.adapters import HTTPAdapter, Retry

from mstrio.api import authentication, exceptions, misc, projects
import mstrio.config as config
from mstrio.utils.helper import deprecation_warning
import mstrio.utils.helper as helper


class Connection(object):
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and
    manages the user's connection with the MicroStrategy REST and Intelligence
    Servers.

    Example:
        >>> from mstrio import connection
        >>>
        >>> # connect to the environment and chosen application
        >>> conn = connection.Connection(
        >>>     base_url="https://demo.microstrategy.com/MicroStrategyLibrary",
        >>>     username="username",
        >>>     password="password",
        >>>     application_name="MicroStrategy Tutorial"
        >>> )
        >>> # disconnect
        >>> conn.close()

    Attributes:
        base_url: URL of the MicroStrategy REST API server.
        username: Username.
        application_name: Name of the connected MicroStrategy Applicaiton.
        application_id: Id of the connected MicroStrategy Applicaiton.
        project_name: (deprecated) Name of the connected MicroStrategy Project.
        project_id: (deprecated) Id of the connected MicroStrategy Project.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates
            with each request.
        user_id: Id of the authenticated user
        user_full_name: Full name of the authenticated user
        user_initials: Initials of the authenticated user
        iserver_version: Version of the I-Server
        web_version: Version of the Web Server
    """
    __VRCH = "11.1.0400"

    def __init__(self, base_url, username=None, password=None, application_name=None,
                 application_id=None, project_name=None, project_id=None, login_mode=1,
                 ssl_verify=True, certificate_path=None, proxies=None, identity_token=None,
                 verbose=True):
        """Establish a connection with MicroStrategy REST API.

        You can establish connection by either providing set of values
        (`username`, `password`, `login_mode`) or just `identity_token`.

        When both `application_id` and `application_name` are `None`,
        application selection is cleared. When both `application_id`
        and `application_name` are provided, `application_name` is ignored.

        Args:
            base_url (str): URL of the MicroStrategy REST API server.
                Typically of the form:
                "https://<mstr_env>.com/MicroStrategyLibrary/api"
            username (str, optional): Username
            password (str, optional): Password
            project_name (str, optional): this argument will be deprecated, use
                application_name instead
            project_id (str, optional): this argument will be deprecated, use
                application_id instead
            application_name (str, optional): Name of the application you intend
                to connect to (case-sensitive). Provide either Application ID
                or Application Name.
            application_id (str, optional): Id of the application you intend to
                connect to (case-sensitive). Provide either Application ID
                or Application Name.
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
        self.session = self.__configure_session(ssl_verify, certificate_path, proxies)
        self._web_version = None
        self._iserver_version = None
        self._user_id = None
        self._user_full_name = None
        self._user_initials = None
        self.__password = password
        application_id = project_id if project_id else application_id
        application_name = project_name if project_name else application_name

        if project_id or project_name:
            deprecation_warning("`project_id` and `project_name`",
                                "`application_id` or `application_name`", "11.3.2.101")

        if self.__check_version():
            # save the version of IServer in config file
            config.iserver_version = self.iserver_version
            # delegate identity token or connect and create new sesssion
            self.delegate() if self.identity_token else self.connect()
            self.select_application(application_id=application_id,
                                    application_name=application_name)
        else:
            print("""This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.
                     \rCurrent Intelligence Server version: {}
                     \rCurrent MicroStrategy Web version: {}
                     """.format(self.iserver_version, self.web_version))
            helper.exception_handler(msg="MicroStrategy Version not supported.",
                                     exception_type=exceptions.VersionException)

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
        deprecation_warning("`select_project` method", "`select_application` method", "11.3.2.101")
        self.select_application(project_id, project_name)

    def select_application(self, application_id: str = None, application_name: str = None) -> None:
        """Select application for the given connection based on application_id
        or application_name.

        When both `application_id` and `application_name` are `None`,
        application selection is cleared. When both `application_id`
        and `application_name` are provided, `application_name` is ignored.

        Args:
            application_id: id of application to select
            application_name: name of application to select

        Raises:
            ValueError: if application with given id or name does not exist
        """
        if application_id is None and application_name is None:
            self.application_id = None
            self.application_name = None
            self.project_id = self.application_id
            self.project_name = self.application_name
            if config.verbose:
                print("No application selected.")
            return None

        if application_id is not None and application_name is not None:
            tmp_msg = ("Both `application_id` and `application_name` arguments provided. "
                       "Selecting application based on `application_id`.")
            helper.exception_handler(msg=tmp_msg, exception_type=Warning)

        _applications = projects.get_projects(connection=self).json()
        if application_id is not None:
            # Find which application name matches the application ID provided
            tmp_applications = helper.filter_list_of_dicts(_applications, id=application_id)
            if not tmp_applications:
                self.application_id, self.application_name = None, None
                tmp_msg = (f"Error connecting to application with id: {application_id}. "
                           "Application with given id does not exist or user has no access.")
                raise ValueError(tmp_msg)
        elif application_name is not None:
            # Find which application ID matches the application name provided
            tmp_applications = helper.filter_list_of_dicts(_applications, name=application_name)
            if not tmp_applications:
                self.application_id, self.application_name = None, None
                tmp_msg = (f"Error connecting to application with name: {application_name}. "
                           "Application with given name does not exist or user has no access.")
                raise ValueError(tmp_msg)

        self.application_id = tmp_applications[0]['id']
        self.application_name = tmp_applications[0]['name']
        self.project_id = self.application_id
        self.project_name = self.application_name
        self.session.headers['X-MSTR-ProjectID'] = self.application_id

    def _get_authorization(self):
        self.__prompt_credentials()
        credentials = "{}:{}".format(self.username, self.__password).encode('utf-8')
        encoded_credential = b64encode(credentials)
        auth = "Basic " + str(encoded_credential, 'utf-8')
        return auth

    def _validate_application_selected(self) -> None:
        if self.application_id is None:
            raise AttributeError(
                "Application not selected. Select application using `select_application` method.")

    def __prompt_credentials(self):
        self.username = self.username if self.username is not None else input("Username: ")
        self.__password = self.__password if self.__password is not None else getpass("Password: ")
        self.login_mode = self.login_mode if self.login_mode else input(
            "Login mode (1 - Standard, 16 - LDAP): ")

    def __check_version(self):
        """Checks version of I-Server and MicroStrategy Web."""
        json_response = misc.server_status(self).json()
        try:
            self._iserver_version = json_response["iServerVersion"][:9]
        except KeyError:
            raise exceptions.IServerException(
                "I-Server is currently unavailable. Please contact your administrator.")
        web_version = json_response.get("webVersion")
        self._web_version = web_version[:9] if web_version else None
        iserver_version_ok = version.parse(self.iserver_version) >= version.parse(self.__VRCH)

        return iserver_version_ok

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

        hooks = []
        if config.debug:
            hooks.append(helper.print_url)
        if config.save_responses:
            hooks.append(helper.save_response)
        if hooks:
            session.hooks['response'] = hooks

        status_forcelist = frozenset([413, 429, 500, 503])  # retry after status

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=Retry.DEFAULT_ALLOWED_METHODS,
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

    def __get_user_info(self):
        response = authentication.get_info_for_authenticated_user(connection=self).json()
        self._user_id = response.get("id")
        self._user_full_name = response.get("fullName")
        self._user_initials = response.get("initials")

    @property
    def user_id(self):
        if not self._user_id:
            self.__get_user_info()
        return self._user_id

    @property
    def user_full_name(self):
        if not self._user_full_name:
            self.__get_user_info()
        return self._user_full_name

    @property
    def user_initials(self):
        if not self._user_initials:
            self.__get_user_info()
        return self._user_initials

    @property
    def web_version(self):
        return self._web_version

    @property
    def iserver_version(self):
        return self._iserver_version

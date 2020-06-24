import os
from packaging import version
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from requests.packages.urllib3.util.retry import Retry

from mstrio.api import authentication, misc, projects
import mstrio.utils.helper as helper
from requests import Session


class Connection(object):
    """Connect to and interact with the MicroStrategy environment.

    Creates a connection object which is used in subsequent requests and manages the user's connection
    with the MicroStrategy REST and Intelligence Servers.

    # import
    from mstrio import microstrategy

    # connect to the environment and chosen project
    conn = connection.Connection(base_url="https://demo.microstrategy.com/MicroStrategyLibrary/api",
                                    username="username",
                                    password="password",
                                    project_name="MicroStrategy Tutorial")

    # disconnect
    conn.close()

    Attributes:
        base_url: URL of the MicroStrategy REST API server.
        username: Username.
        password: Password.
        project_name: Name of the connected MicroStrategy Project.
        project_id: Id of the connected MicroStrategy Project.
        login_mode: Authentication mode. Standard = 1 (default) or LDAP = 16.
        ssl_verify: If True (default), verifies the server's SSL certificates with each request.
    """
    __VRCH = "11.1.0400"
    __DEFAULT_METHOD_WHITELIST = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])
    __RETRY_AFTER_STATUS_CODES = frozenset([413, 429, 500, 503])

    def __init__(self, base_url=None, username=None, password=None, project_name=None, project_id=None, login_mode=1,
                 ssl_verify=True, certificate_path=None, proxies=None, identity_token=None, verbose=True):
        """
        Establishes a connection with MicroStrategy REST API.

        Args:
            base_url (str, optional): URL of the MicroStrategy REST API server. Typically of the form
            https://<mstr_env>.com/MicroStrategyLibrary/api
            username (str, optional): Username
            password (str, optional): Password
            project_name (str, optional): Name of the project you intend to connect to.Case-sensitive.
                            You should provide either Project ID or Project Name.
            project_id (str, optional): Id of the project you intend to connect to. Case-sensitive.
                            You should provide either Project ID or Project Name.
            login_mode (int, optional): Specifies the authentication mode to use. Supported authentication modes are:
                            Standard (1) (default) or LDAP (16)
            ssl_verify (bool, optional): If True (default), verifies the server's SSL certificates with each request
            certificate_path (str, optional): Path to SSL certificate file, if None and ssl_verify is True then the
                            certificate will be looked for in current working directory
            proxies (dict, optional): Dictionary mapping protocol or protocol and host to the URL of the proxy
                            (e.g. {'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'})
            identity_token (str, optional): Identity token for delegated session. Used for connection initialized
                            by GUI.
            verbose (bool, optional): True by default. Controls the amount of feedback from the I-Server.
        """

        self.base_url = helper.url_check(base_url)
        self.username = username
        self.password = password
        if project_id is not None and project_name is not None:
            helper.exception_handler(msg="Provide either Project ID or Project Name.", exception_type=ValueError)
        else:
            self.project_id = project_id
            self.project_name = project_name
        self.login_mode = login_mode
        self.web_version = None
        self.iserver_version = None
        self.verbose = verbose
        self.certificate_path = certificate_path
        self.identity_token = identity_token
        self.session = self.__configure_session(ssl_verify, certificate_path, proxies)

        if self.__check_version():
            # delegate identity token or connect and create new sesssion
            self.delegate() if self.identity_token else self.connect()
            self.__select_project()
        else:
            print("""This version of mstrio is only supported on MicroStrategy 11.1.0400 or higher.
                    /rCurrent Intelligence Server version: {}
                    /rCurrent MicroStrategy Web version: {}
                    """.format(self.iserver_version, self.web_version))
            helper.exception_handler(msg="MicroStrategy Version not supported.",
                                     exception_type=VersionException)

    def connect(self):
        """Authenticates the user and creates a new connection with the Intelligence Server. If an active connection is
        detected, the session is renewed"""
        response = authentication.session_renew(connection=self, verbose=helper.debug())
        if not response.ok:
            response = authentication.login(connection=self, verbose=helper.debug())
            self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
            if self.verbose:
                print("Connection to MicroStrategy Intelligence Server has been established.")
        else:
            if self.verbose:
                print("Connection to MicroStrategy Intelligence Server was renewed.")

    def delegate(self):
        """Delegates identity token to get authentication token and connect to MicroStrategy Intelligence Server."""
        response = authentication.delegate(self, self.identity_token)
        self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
        if self.verbose:
            print("Connection with MicroStrategy Intelligence Server has been delegated.")

    def get_identity_token(self):
        """Create new identity token using existing authentication token"""
        response = authentication.identity_token(self)
        return response.headers['X-MSTR-IdentityToken']

    def close(self):
        """Closes a connection with MicroStrategy REST API"""
        authentication.logout(connection=self, verbose=helper.debug())

        if self.verbose:
            print("Connection to MicroStrategy Intelligence Server has been closed")

    def renew(self):
        """Checks if the session is still alive. If so, renews the session and extends session expiration."""
        status = authentication.session_renew(connection=self, verbose=helper.debug())

        if status.status_code == 204:
            if self.verbose:
                print("Your connection to MicroStrategy Intelligence Server was renewed.")
        else:
            response = authentication.login(connection=self, verbose=helper.debug())
            self.session.headers['X-MSTR-AuthToken'] = response.headers['X-MSTR-AuthToken']
            if self.verbose:
                print("""Connection with MicroStrategy Intelligence Server was not active.
                         \rNew connection has been established.""")

    def status(self):
        """Checks if the session is still alive."""
        status = authentication.session_status(connection=self, verbose=helper.debug())

        if status.status_code == 200:
            print("Connection to MicroStrategy Intelligence Server is active.")
        else:
            print("Connection to MicroStrategy Intelligence Server is not active.")

    def __select_project(self):
        # Fetch the list of projects the user has access to
        msg = "Error connecting to project '{}'. Check project name and try again.".format(self.project_name)
        response = projects.projects(connection=self, error_msg=msg, verbose=helper.debug())

        # Find which project ID matches the project name provided
        _projects = response.json()

        if self.project_name is not None:
            # Find which project ID matches the project name provided
            for _project in _projects:
                if _project['name'] == self.project_name:  # Enter the desired project name here
                    self.project_id = _project['id']
        else:
            # Find which project name matches the project ID provided
            for _project in _projects:
                if _project['id'] == self.project_id:  # Enter the desired project id here
                    self.project_name = _project['name']
        self.session.headers['X-MSTR-ProjectID'] = self.project_id

    def __check_version(self):
        """Checks version of I-Server and MicroStrategy Web"""
        response = misc.server_status(self)

        json_response = response.json()
        self.iserver_version = json_response["iServerVersion"][:9]
        self.web_version = json_response["webVersion"][:9]

        iserver_version_ok = version.parse(self.iserver_version) >= version.parse(self.__VRCH)
        web_version_ok = version.parse(self.web_version) >= version.parse(self.__VRCH)

        return iserver_version_ok and web_version_ok

    def __configure_session(self, verify, certificate_path, proxies, existing_session=None, retries=3,
                            backoff_factor=0.5, status_forcelist=None, method_whitelist=None):
        """Creates a shared requests.Session() object with configuration from the initialization. Additional
        parameters change how the HTTPAdapter is configured.

        Args:
            existing_session (requests.Session() object, optional): Optional existing Session object to configure
            retries (int, optional): number of retries for certain type of requests (i.e. get)
            backoff_factor (float, optional):  backoff factor to apply between attempts after the second try
                (most errors are resolved immediately by a second try without a delay). urllib3 will sleep for:
                {backoff factor} * (2 ^ ({number of total retries} - 1)) seconds. If the backoff_factor is 0.1,
                then sleep() will sleep for [0.0s, 0.2s, 0.4s, ...] between retries. It will never be longer
                than Retry. BACKOFF_MAX. By default, backoff is disabled (set to 0).
            status_forcelist: list of http statuses that will be retried
        """
        session = existing_session or Session()
        session.proxies = proxies if proxies is not None else {}
        session.verify = self._configure_ssl(verify, certificate_path)

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


class VersionException(Exception):
    pass

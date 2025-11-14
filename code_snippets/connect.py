"""
This demo script shows how to connect to Strategy One Environment. This script
will not work without replacing parameters with real values. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import (
    get_connection, Connection, Timeout, ConnectTimeout, ReadTimeout
)
from mstrio import config

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

# The Connection object manages your connection to Strategy One. Connect to
# your Strategy One environment by providing the URL to the Strategy One REST
# API server, your username, password and the ID of the Project to connect to.
# When a Connection object is created the user will be automatically logged-in.
# Connection object automatically renews the connection or reconnects,
# if session becomes inactive. Reconnection doesn't work if authenticated with
# identity token.
conn = get_connection(workstationData, project_name=PROJECT_NAME)
# The URL for the REST API server typically follows this format:
# https://your-microstrategy-server.com/MicroStrategyLibrary/api

# Validate that the REST API server is running by accessing
# https://your-microstrategy-server.com/MicroStrategyLibrary/api-docs in your
# web browser.

# To manage the connection the following methods are made available:
conn.connect()  # triggered by default during Connection class initialization
conn.renew()  # alias for `connect`
conn.open()  # alias for `connect`

conn.close()
conn.disconnect()  # alias for `close`

conn.status()

# Define variables which can be later used in a script
BASE_URL = $base_url  # Insert URL for your env here
MSTR_USERNAME = $mstr_username  # Insert your env username here
MSTR_PASSWORD = $mstr_password  # insert your mstr password here
PROJECT_ID = $project_id  # Insert you project ID here

# Authentication Methods
# Currently, supported authentication modes are Standard (the default), LDAP and API Token.

# To use LDAP, add login_mode=16 when creating your Connection object:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, login_mode=16)

# Define a variable which can be later used in a script
API_TOKEN = $api_token  # insert your api token here

# To use API Token, just provide it to your Connection object via `api_token=` parameter:
# If API Token is provided, login mode will automatically be set to 4096.
# The identity token can be obtained by sending a request to
# Strategy One REST API /auth/apiTokens endpoint.
conn = Connection(BASE_URL, api_token=API_TOKEN, project_id=PROJECT_ID)

# Once logged in, regardless of the method used, you can generate API Token for yourself
# by using the below method:
api_token = conn.get_api_token()
# Some users can create API Tokens for other users. Learn more in `user_mgmt.py` code snippets.

# Define a variable which can be later used in a script
IDENTITY_TOKEN = $identity_token  # Insert your identity token here

# Optionally, the Connection object can be created by passing the IDENTITY_TOKEN
# parameter, which will create a delegated session. The identity token can be
# obtained by sending a request to Strategy One REST API /auth/identityToken
# endpoint.
conn = Connection(BASE_URL, identity_token=IDENTITY_TOKEN, project_id=PROJECT_ID)

# SSL Self - signed Certificate
# By default, SSL certificates are validated with each API request.
# To turn this off, use ssl_verify flag:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, ssl_verify=False)

# If you are using an SSL with a self-signed certificate you will need to
# perform an additional step to configure your connection. There are 2 ways to
# set it up:

# The easiest way to configure the SSL is to move your certificate file to your
# working directory. Just make sure the ssl_verify parameter is set to True when
# creating the Connection object in mstrio - py(it is True by default):
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, ssl_verify=True)

# Define a variable which can be later used in a script
CERTIFICATE_PATH = $certificate_path  # Insert your certificate path here

# The second way is to pass the certificate_path parameter to your connection
# object in mstrio. It has to be the absolute path to your certificate file:
conn = Connection(
    BASE_URL,
    MSTR_USERNAME,
    MSTR_PASSWORD,
    project_id=PROJECT_ID,
    certificate_path=CERTIFICATE_PATH
)

# Retries and Request Timeout
# You may want to set some retry logic or timeout for requests done in your
# scripts by mstrio-py.
#
# Keep in mind, those settings are for "per request" and DO NOT apply to server
# timeout or machine timeout (like runtimes in Workstation)
#
# You can set them by any of the below ways:
#
# set global config value (only for request timeout, not retries):
# (learn more about mstrio-py's config in `config_mgmt.py` code snippet)
config.default_request_timeout = 60 * 10  # value in seconds == 10min, for example
#
# set parameters during `Connection` initialization:
conn = Connection(
    BASE_URL,
    MSTR_USERNAME,
    MSTR_PASSWORD,
    request_timeout=60 * 10,  # value in seconds == 10min, for example
    request_retry_on_timeout_count=3,
)
#
# set parameters on existing `conn` instance:
conn.set_request_timeout(60 * 10)  # value in seconds == 10min, for example
conn.set_request_retry_on_timeout_count(3)
#
# once set, if hit the timeout will raise `requests.Timeout` error.
# this is a `requests` library's custom error that mstrio-py just reuses.
# It can be either `Timeout` or specifically `ConnectTimeout` or `ReadTimeout`.
# They can be than caught and handled, if needed:
try:
    # some action that does a REST API request
    do_something(connection=conn)
except ConnectTimeout as err:
    # this will catch only connection timeouts, raised if no response was
    # received from server within timeout period
    ...
except ReadTimeout as err:
    # this will catch only read timeouts, raised if server did not send all data
    # within timeout period
    ...
except Timeout as err:
    # this will catch all of them: `Timeout`, `ConnectTimeout`, `ReadTimeout`
    ...

# Define variables which can be later used in a script
PROXIES_HTTP_VALUE = $proxies_http_value  # f.e. 'foo.bar:3128'
PROXIES_HTTPS_KEY = $proxies_https_key  # f.e. 'https://host.name'
PROXIES_HTTPS_VALUE = $proxies_https_value # f.e. 'foo.bar:4012'
PROXIES = {'http': PROXIES_HTTP_VALUE, PROXIES_HTTPS_KEY: PROXIES_HTTPS_VALUE }
# f.e. 'https://<username>:<password>@<ip_address>:<port>/'
PROXIES_HTTP_VALUE_USERNAME_AND_PASSWORD = $proxies_http_value_username_and_password

# Proxy
# Optionally, proxy settings can be set for the Strategy One Connection object.
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, proxies=PROXIES)

# User can also specify username and password in proxies parameter to use HTTP
# Basic Auth:
proxies = {'http': PROXIES_HTTP_VALUE_USERNAME_AND_PASSWORD}
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, proxies=proxies)

# There might be situations where you want to temporarily unselect a project in
# your `Connection` object or select a different one. In such cases, you can use
# a helper method as below.
with conn.temporary_project_change(project=None):
    ...
    # inside `with` block code will work on `conn` without project selected
    ...
...
# outside, this code is back to use `conn` with `PROJECT_NAME` selected earlier
...

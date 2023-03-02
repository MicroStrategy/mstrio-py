"""
This demo script shows how to connect to MicroStrategy Environment. This script
will not work without replacing parameters with real values. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection, Connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

# The Connection object manages your connection to MicroStrategy. Connect to
# your MicroStrategy environment by providing the URL to the MicroStrategy REST
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
conn.connect()
conn.close()
conn.status()

# Define variables which can be later used in a script
BASE_URL = $base_url  # Insert URL for your env here
MSTR_USERNAME = $mstr_username  # Insert your env username here
MSTR_PASSWORD = $mstr_password  # insert your mstr password here
PROJECT_ID = $project_id  # Insert you project ID here

# Authentication Methods
# Currently, supported authentication modes are Standard (the default) and LDAP.
# To use LDAP, add login_mode=16 when creating your Connection object:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, login_mode=16)

# Define a variable which can be later used in a script
IDENTITY_TOKEN = $identity_token  # Insert your identity token here

# Optionally, the Connection object can be created by passing the IDENTITY_TOKEN
# parameter, which will create a delegated session. The identity token can be
# obtained by sending a request to MicroStrategy REST API /auth/identityToken
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

# Define variables which can be later used in a script
PROXIES_HTTP_VALUE = $proxies_http_value  # f.e. 'foo.bar:3128'
PROXIES_HTTPS_KEY = $proxies_https_key  # f.e. 'https://host.name'
PROXIES_HTTPS_VALUE = $proxies_https_value # f.e. 'foo.bar:4012'
PROXIES = {'http': PROXIES_HTTP_VALUE, PROXIES_HTTPS_KEY: PROXIES_HTTPS_VALUE }
# f.e. 'https://<username>:<password>@<ip_address>:<port>/'
PROXIES_HTTP_VALUE_USERNAME_AND_PASSWORD = $proxies_http_value_username_and_password

# Proxy
# Optionally, proxy settings can be set for the MicroStrategy Connection object.
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, proxies=PROXIES)

# User can also specify username and password in proxies parameter to use HTTP
# Basic Auth:
proxies = {'http': PROXIES_HTTP_VALUE_USERNAME_AND_PASSWORD}
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID, proxies=proxies)

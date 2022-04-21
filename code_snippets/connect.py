"""
This demo script shows how to connect to MicroStrategy Environment. This script
will not work without replacing parameters with real values. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection,Connection

PROJECT_NAME = '<Project_name>'
BASE_URL = '<URL>' # Insert URL for your env here
MSTR_USERNAME = '<Username>' # Insert your env username here
MSTR_PASSWORD = '<Password>' # insert your mstr password here
PROJECT_ID='<Project_ID>' # Insert you project ID here
IDENTITY_TOKEN = '<Identtity_Token>' # Insert your identity token here
CERTIFICATE_PATH = "C:/path/to/your/certificate.pem" # Insert your certificate path here
PROXIES = {'http': 'foo.bar:3128', 'https://host.name': 'foo.bar:4012'} # Edit your proxies here

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

# Authentication Methods
# Currently, supported authentication modes are Standard (the default) and LDAP.
# To use LDAP, add login_mode=16 when creating your Connection object:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  login_mode=16)

# Optionally, the Connection object can be created by passing the IDENTITY_TOKEN
# parameter, which will create a delegated session. The identity token can be
# obtained by sending a request to MicroStrategy REST API /auth/identityToken
# endpoint.
conn = Connection(BASE_URL, identity_token=IDENTITY_TOKEN, project_id=PROJECT_ID)

# SSL Self - signed Certificate
# By default, SSL certificates are validated with each API request.
# To turn this off, use ssl_verify flag:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  ssl_verify=False)

# If you are using an SSL with a self-signed certificate you will need to
# perform an additional step to configure your connection. There are 2 ways to
# set it up:

# The easiest way to configure the SSL is to move your certificate file to your
# working directory. Just make sure the ssl_verify parameter is set to True when
# creating the Connection object in mstrio - py(it is True by default):
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  ssl_verify=True)

# The second way is to pass the certificate_path parameter to your connection
# object in mstrio. It has to be the absolute path to your certificate file:
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  certificate_path=CERTIFICATE_PATH)

# Proxy
# Optionally, proxy settings can be set for the MicroStrategy Connection object.
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  proxies=PROXIES)

# User can also specify username and password in proxies parameter to use HTTP
# Basic Auth:
proxies = {'http': 'https://<username>:<password>@<ip_address>:<port>/'}
conn = Connection(BASE_URL, MSTR_USERNAME, MSTR_PASSWORD, project_id=PROJECT_ID,
                  proxies=proxies)

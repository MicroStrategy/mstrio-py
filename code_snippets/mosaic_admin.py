"""This is the demo script to show how to manage Mosaic SSO settings.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.server.mosaic import (
    MosaicSsoSettings,
    commit_mosaic_settings,
    get_mosaic_settings,
    stage_mosaic_settings,
    upload_mosaic_keytab,
)

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert name of project here

conn = get_connection(connectionData, project_id=PROJECT_ID)

# Get the current Mosaic SSO settings
# The `status` field tells where the settings come from:
# 'IN_PROGRESS' - draft settings from the sidecar file
# 'COMMITTED' - settings from the production config files
settings = get_mosaic_settings(connection=conn)
print(settings)

# Define variables which can be later used in a script
KEYTAB_FILE_PATH = $keytab_file_path  # Insert path to the keytab file here
KEYTAB_FILE_NAME = $keytab_file_name  # e.g. 'mci-jpd9h-dev-http.keytab'

# Upload a Mosaic keytab file to the local shared folder so other services
# can access it. The file can be provided as a path (str or Path) - then
# the file name defaults to the base name of the path - or as bytes with
# an explicit file name.
upload_mosaic_keytab(connection=conn, file=KEYTAB_FILE_PATH)
upload_mosaic_keytab(
    connection=conn,
    file=open(KEYTAB_FILE_PATH, 'rb').read(),
    file_name=KEYTAB_FILE_NAME,
)

# Define variables which can be later used in a script
KRB5_REALM = $krb5_realm  # uppercase FQDN, e.g. 'CORP.MICROSTRATEGY.COM'
MOSAIC_HOST = $mosaic_host  # e.g. 'demo.microstrategy.com'
UPN_DOMAIN = $upn_domain  # first entry is used as email suffix

# Build the Mosaic SSO settings
# The read-only `status` field is stripped automatically before sending
new_settings = MosaicSsoSettings(
    krb5_realm=KRB5_REALM,
    mosaic_host=MOSAIC_HOST,
    keytab_file_name=KEYTAB_FILE_NAME,
    upn_domains=[UPN_DOMAIN],
)

# Save draft Mosaic settings to a sidecar file without modifying
# production config files
stage_mosaic_settings(connection=conn, settings=new_settings)

# Commit Mosaic settings to production config files
# The server will update config.properties, krb5.conf and user-mapping.json
# under universal semantic service and enable JWT authentication mode
commit_mosaic_settings(connection=conn, settings=new_settings)

# Settings can also be provided as a plain dictionary (camelCase keys)
commit_mosaic_settings(
    connection=conn,
    settings={
        'krb5Realm': KRB5_REALM,
        'mosaicHost': MOSAIC_HOST,
        'keytabFileName': KEYTAB_FILE_NAME,
        'upnDomains': [UPN_DOMAIN],
    },
)

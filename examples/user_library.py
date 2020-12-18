"""This is the demo script to show how administrator can manage documents and
dossiers in users' libraries.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.admin.document import Document, list_documents
from mstrio.admin.dossier import Dossier, list_dossiers
from mstrio.admin.user import User, list_users
from mstrio.admin.usergroup import UserGroup, list_usergroups
from mstrio.connection import Connection

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name='MicroStrategy Library', login_mode=1)

# list all dossiers and documents within a project to which we have connection
dossiers = list_dossiers(connection=conn)
docs = list_documents(connection=conn)

# get document and dossier from by name or id and publish them to a library of an authenticated user
doc = Document(connection=conn, name='Some Simple Document')
doss = Dossier(connection=conn, name='Some Simple Dossier')
doc.publish()
doss.publish()

# list all users and get 2 of them
users = list_users(connection=conn)
user_1 = User(connection=conn, id='1234234534564567567867897890ABCD')
user_2 = User(connection=conn, id='9876876576546543543243213210DCBA')

# share one dossier/document to a given user(s) by passing user object(s) or id(s)
doss.publish(recipients=user_1)
doss.publish(recipients=['1234234534564567567867897890ABCD', '9876876576546543543243213210DCBA'])
# analogously we can take away dossier(s)/document(s) from the library of the given user(s)
doss.unpublish(recipients=[user_1, user_2])
doss.unpublish(recipients='1234234534564567567867897890ABCD')

# list all usergroups and get one of them
usrgrps = list_usergroups(connection=conn)
usrgrp = UserGroup(connection=conn, name='Data Scientists')

# add users to given usergroup
usrgrp.add_users(users=[user_1, user_2])

# get documents with given ids to give to the usergroup and users which belong to it
docs_to_publish = list_documents(connection=conn, id=['12340987234598763456876545677654',
                                                      '98761234876523457654345665434567',
                                                      '654356785432678943217890ABCDDCBA'])
for doc in docs_to_publish:
    doc.publish(recipients=usrgrp)

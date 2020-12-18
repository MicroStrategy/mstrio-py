"""This is the demo script to show how administrator can manage subscriptions
and schedules.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.admin.subscription.subscription import Subscription, EmailSubscription
from mstrio.admin.subscription.content import Content
from mstrio.admin.subscription.subscription_manager import SubscriptionManager, list_subscriptions
from mstrio.admin.schedule import Schedule, ScheduleManager

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, login_mode=1)

# create manager for subscriptions on a chosen application
sub_mngr = SubscriptionManager(connection=conn, application_name='MicroStrategy Tutorial')
# get all subscriptions from the given application (it is possible in two ways)
all_subs = list_subscriptions(connection=conn, application_name='MicroStrategy Tutorial')
all_subs = sub_mngr.list_subscriptions()

#  execute/delete subscriptions by passing theirs ids or Subscription objects
sub_mngr.execute(['11223344556677889900AABBCCDDEEFF', 'FFEEDDCCBBAA00998877665544332211'])
sub_mngr.delete(['11223344556677889900AABBCCDDEEFF', 'FFEEDDCCBBAA00998877665544332211'])

# list available recipients of the subscription for the given content (default delivery type is an email)
sub_mngr.available_recipients(content_id='11112222333344445555666677778888', content_type='DOCUMENT')

# get a single subscription
sub = Subscription(connection=conn,
                   subscription_id='AA11BB22CC33DD44EE55FF6677889900',
                   application_id='00FF99EE88DD77CC66BB55AA44332211')
# list all recipients of the given subscription and all available for this subscription
sub.recipients
sub.available_recipients()

# add/remove recipient(s) with given id(s)
sub.add_recipient(recipients=['1234567890A1234567890A1234567890', '98765432198765432198765432198765'])
sub.remove_recipient(recipients=['1234567890A1234567890A1234567890', '98765432198765432198765432198765'])

# execute a given subscription
sub.execute()

# replace a user with an admin in all of its subscriptions (e.g. when user exits company)
for s in sub_mngr.list_subscriptions(to_dictionary=False):
    if '9871239871298712413241235643132A' in [r['id'] for r in s.recipients]:
        s.add_recipient(recipients='11111111111111111111111111111111')
        s.remove_recipient(recipients='9871239871298712413241235643132A')

# create an email subscription
EmailSubscription.create(
    connection=conn, name="New Email Subscription for a Report", application_name="MicroStrategy Tutorial",
    contents=Content(id='ABC123ABC123ABC123ABC123ABC12345', type=Content.Type.REPORT),
    schedules_ids=['ABC123ABC123ABC123ABC123ABC12345'], recipients=['ABC123ABC123ABC123ABC123ABC12345'])

# get list of schedules (you can filter them by for example name, id or description)
schdl_mngr = ScheduleManager(connection=conn)
all_schdls = schdl_mngr.list_schedules()

# get a single schedule by its id or name and then its properties
schdl = Schedule(connection=conn, name='Some shedule which runs daily')
schdl.list_properties()

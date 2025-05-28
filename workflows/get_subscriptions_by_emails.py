"""
Get subscriptions by user emails.

1. Connect to the environment using data from workstation
2. Specify emails to search for in subscriptions
3. Get all subscriptions and iterate over them
4. Iteration over all user's recipients of the subscription
5. Try to get the addresses of the user from the response with subscriptions
6. If the user is not in the response with subscriptions get its addresses
7. Iterate over all email addresses of the user and print message with
   information about the subscription name and id and user email
"""

from mstrio.connection import Connection, get_connection
from mstrio.distribution_services import list_subscriptions
from mstrio.utils.response_processors import users


def get_subscriptions_by_emails(connection: 'Connection', emails: list[str]) -> None:
    """Get subscriptions by user emails.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        emails (list[str]): List of emails to search for in subscriptions.
    """
    user_addresses = {}
    for sub in list_subscriptions(connection=connection):
        # Iterate over all user recipients of the subscription
        for user_id in [x['id'] for x in sub.recipients if x['type'] == 'user']:
            try:
                # Try to get the addresses of the user from the dictionary
                # to reduce the number of API calls
                addresses = user_addresses[user_id]
            except KeyError:
                # If the user is not in the dictionary, get the addresses from the API
                addresses = users.get_addresses(conn, id=user_id)['addresses']
                # Store the addresses in the dictionary for future use
                user_addresses[user_id] = addresses
            # Iterate over all email addresses of the user
            for email in [
                addr['physicalAddress']
                for addr in addresses
                if addr['deliveryType'] == 'email' and addr['physicalAddress'] in emails
            ]:
                print(
                    f'Found in subscription: {sub.name} with ID: {sub.id}, '
                    f'user email: {email}'
                )


# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

emails_to_find = ['user_1@email.com', 'user_2@email.com']

get_subscriptions_by_emails(conn, emails_to_find)

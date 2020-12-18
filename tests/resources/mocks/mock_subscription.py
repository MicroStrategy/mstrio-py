import json
from unittest.mock import Mock
from copy import deepcopy

class MockSubscription:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    @classmethod
    def mock_subscriptions_api(cls):

        with open(cls.data_paths['subscriptions']['subscriptions']) as f:
            cls.subscriptions_data = json.load(f)

        with open(cls.data_paths['subscriptions']['get_subscription']) as f:
            cls.subscription_data = json.load(f)

        with open(cls.data_paths['subscriptions']['create']) as f:
            cls.create_data = json.load(f)

        with open(cls.data_paths['subscriptions']['update']) as f:
            cls.update_data = json.load(f)

        with open(cls.data_paths['subscriptions']['available_recipients']) as f:
            cls.recipients_data = json.load(f)

        with open(cls.data_paths['subscriptions']['bursting']) as f:
            cls.bursting_data = json.load(f)

        def mocked_list_subscriptions(*args):
            mocked_list_subscriptions = Mock(status_code=200)
            mocked_list_subscriptions.json.return_value = cls.subscriptions_data
            return mocked_list_subscriptions

        def mocked_get_subscription(*args):
            mocked_get_subscription = Mock(status_code=200)
            mocked_get_subscription.json.return_value = cls.subscription_data
            return mocked_get_subscription

        def mocked_create_subscription(*args):
            mocked_create_subscription = Mock(status_code=200)
            mocked_create_subscription.json.return_value = cls.create_data
            return mocked_create_subscription

        def mocked_update_subscription(*args):
            mocked_update_subscription = Mock(status_code=200)

            update_data = cls.update_data
            recipients = args[3].get('recipients')
            if recipients:
                update_data['recipients'] = recipients

            mocked_update_subscription.json.return_value = cls.update_data

            return mocked_update_subscription

        def mocked_available_recipients(*args):
            mocked_available_recipients = Mock(status_code=200)
            mocked_available_recipients.json.return_value = cls.recipients_data
            return mocked_available_recipients

        def mocked_list_available_bursting(*args):
            mocked_list_available_bursting = Mock(status_code=200)
            mocked_list_available_bursting.json.return_value = cls.bursting_data
            return mocked_list_available_bursting

        def mocked_remove_subscription(*args):
            mocked_remove_subscription = Mock(status_code=204)
            return mocked_remove_subscription

        mocked_subscriptions = Mock()
        mocked_subscriptions.list_subscriptions = mocked_list_subscriptions
        mocked_subscriptions.get_subscription = mocked_get_subscription
        mocked_subscriptions.create_subscription = mocked_create_subscription
        mocked_subscriptions.update_subscription = mocked_update_subscription
        mocked_subscriptions.available_recipients = mocked_available_recipients
        mocked_subscriptions.bursting_attributes = mocked_list_available_bursting
        return mocked_subscriptions

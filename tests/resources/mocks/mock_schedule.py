import json
from unittest.mock import Mock


class MockSchedule:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['schedules']['schedules']) as f:
        schedules_data = json.load(f)

    with open(data_paths['schedules']['schedule']) as f:
        schedule_data = json.load(f)

    @classmethod
    def mock_schedules_api(cls):

        def mocked_list_schedules(*args):
            mocked_list_schedules = Mock(status_code=200)
            mocked_list_schedules.json.return_value = cls.schedules_data
            return mocked_list_schedules

        def mocked_get_schedule(*args):
            mocked_get_schedule = Mock(status_code=200)
            mocked_get_schedule.json.return_value = cls.schedule_data
            return mocked_get_schedule

        mocked_schedules = Mock()
        mocked_schedules.list_schedules = mocked_list_schedules
        mocked_schedules.get_schedule = mocked_get_schedule

        return mocked_schedules

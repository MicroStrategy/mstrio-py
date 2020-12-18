from unittest import TestCase

from mstrio.admin import schedule
from mstrio.admin.schedule import Schedule, ScheduleManager
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_schedule import MockSchedule


class TestSubscription(TestCase):

    @classmethod
    def setUpClass(cls):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        schedule.schedules = MockSchedule.mock_schedules_api()

        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')
        cls.sub_id = 'C9073B9011EB0FB792170080EF45BE34'
        cls.app_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_list_schedules(self):
        sch = ScheduleManager(self.connection)
        schedules = sch.list_schedules()
        self.assertEqual(len(schedules), 14)
        self.assertEqual(schedules[0]['id'], 'FF7BB3C811D501F0C00051916B98494F')

    def test_list_schedule_properties(self):
        s = Schedule(self.connection, 'FF7BB3C811D501F0C00051916B98494F')
        s.list_properties
        self.assertEqual(s.id, 'FF7BB3C811D501F0C00051916B98494F')
        self.assertEqual(s.name, 'All the Time')
        self.assertEqual(s.schedule_type, 'time_based')

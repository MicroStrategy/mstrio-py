"""This is the demo script to show how administrator can manage schedules
and events.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services import (Event, list_events, list_schedules, list_subscriptions,
                                          Schedule, ScheduleEnums, ScheduleTime, Subscription)

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, login_mode=1)

# get list of all schedules
all_schedules = list_schedules(connection=conn)
# get all event based schedules
event_based_schedules = list_schedules(connection=conn,
                                       schedule_type=Schedule.ScheduleType.EVENT_BASED.value)
# get all expired Schedules
expired_schedules = list_schedules(connection=conn, expired=True)

# get all events
events = list_events(connection=conn)

# get single Schedule and list its properties
schedule = Schedule(connection=conn, id='AA11BB22CC33DD44EE55FF6677889900')
scheudle = Schedule(connection=conn, name='On Database Load')
schedule.list_properties()

# get single Event and list its properties
event = Event(connection=conn, name='Event1')
event.list_properties()

# disable/enable(pass new schedule expire time)
schedule.disable()
schedule.enable("2021-12-31")

# alter schedule properties
schedule.alter(description="New description")
# altering schedule type is also possible;
# changing event based schedule to time based (using ScheduleTime class):
schedule_time = ScheduleTime.from_details(
    recurrence_pattern=ScheduleEnums.RecurrencePattern.MONTHLY,
    monthly_pattern=ScheduleEnums.MonthlyPattern.DAYS_OF_MONTH,
    days_of_month=['1', '3', '10', '28'], repeat_interval=2,
    execution_pattern=ScheduleEnums.ExecutionPattern.ONCE, execution_time='02:00:00')
schedule.alter(time=schedule_time)

# create time based schedule
new_schedule = Schedule.create(
    connection=conn, name='Test Schedule', schedule_type=Schedule.ScheduleType.TIME_BASED,
    start_date='2021-06-24', recurrence_pattern=ScheduleEnums.RecurrencePattern.DAILY,
    repeat_interval=2, daily_pattern=ScheduleEnums.DailyPattern.DAILY,
    execution_pattern=ScheduleEnums.ExecutionPattern.ONCE, execution_time='02:00:00')
# create event based schedule
new_schedule = Schedule(connection=conn, name='Test Schedule',
                        schedule_type=Schedule.ScheduleType.EVENT_BASED, event=event,
                        start_date='2021-06-24', stop_date='2022-01-01')

# delete schedule
# (Note: deleting schedule will also delete related subscriptions!)
schedule.delete()

# good practice is to check if subscription is using the schedule,
# which we want to delete and if so alter it before deletion
other_schedule = Schedule(connection=conn, name="Some other schedule")
sub1 = Subscription(connection=conn, subscription_id='AA11BB22CC33DD44EE55FF6677889900',
                    project_id='00FF99EE88DD77CC66BB55AA44332211')
sub1.alter(schedules=other_schedule)

# get a list of subscriptions using schedule under the given project
all_subscriptions = list_subscriptions(conn, project_name='Sample Project')
subs_with_schedule = [sub for sub in all_subscriptions if sub.schedules[0].id == schedule.id]

# delete all expired schedules - user will be prompted to confirm every deletion
# (Note: deleting schedule will also delete related subscriptions!)
expired_schedules = list_schedules(connection=conn, expired=True)
for sch in expired_schedules:
    sch.delete()

# changing schedules for multiple subscriptions can be easily done using simple
# for loop (batch execution substitute)
sub2 = Subscription(connection=conn, subscription_id='XX11BB22CC33DD44EE55FF6677889900',
                    project_id='00FF99EE88DD77CC66BB55AA44332211')
list_of_subscriptions = [sub1, sub2]
for subscription in list_of_subscriptions:
    subscription.alter(schedules=schedule)

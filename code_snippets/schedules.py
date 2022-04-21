"""This is the demo script to show how administrator can manage schedules
and events.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import (list_schedules, list_subscriptions, Schedule,
                                          ScheduleEnums, ScheduleTime, Subscription)
from mstrio.distribution_services import Event, list_events
from mstrio.connection import get_connection
from mstrio.utils.wip import module_wip, WipLevels

# Currently there is no way to delete schedules with a script in Workstation.
# The functionality can be used in standalone Python runtime.
# TODO remove wip when Input functionality will be implemented to WS-Scripts
module_wip(globals(), level=WipLevels.WARNING)

PROJECT_NAME = '<Project_name>'  # Project to connect to
SCHEDULE_ID = '<Schedule_ID>'  # id for Schedule object lookup
SCHEDULE_NAME = '<Name_of_schedule>'  # name for Schedule object

SCHEDULE_EVENT_NAME = '<Name_of_event>'  # name of existing event to base a schedule on

SCHEDULE_TYPE = Schedule.ScheduleType.TIME_BASED  # see distribution_services/device/schedule.py for possible values
SCHEDULE_START_DATE = '<Date>'  # YYYY-MM-DD format
SCHEDULE_STOP_DATE = '<Date>'  # YYYY-MM-DD format
SCHEDULE_EXECUTE_TIME = '<Time>'  # HH:MM:SS format
SUBSCRIPTION_ID = '<Subscription_ID>'  # id for Subscription object lookup

# properties to alter schedule with
SCHEDULE_EXPIRE_TIME = '<Date>'  # YYYY-MM-DD format
SCHEDULE_DESCRIPTION = '<Description_of_schedule>'
SCHEDULE_TIME = ScheduleTime.from_details(
    recurrence_pattern=ScheduleEnums.RecurrencePattern.MONTHLY,
    monthly_pattern=ScheduleEnums.MonthlyPattern.DAYS_OF_MONTH,
    days_of_month=['1', '3', '10', '28'], repeat_interval=2,
    execution_pattern=ScheduleEnums.ExecutionPattern.ONCE, execution_time=SCHEDULE_EXECUTE_TIME)
# see distribution_services/schedule/schedule_time.py for RecurrencePattern,
# MonthlyPattern and ExecutionPattern values

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# get list of all schedules
all_schedules = list_schedules(connection=conn)

# get all event based schedules
event_based_schedules = list_schedules(connection=conn,
                                       schedule_type=Schedule.ScheduleType.EVENT_BASED.value)
# see distribution_services/device/schedule.py for ScheduleType values

# get all expired Schedules
expired_schedules = list_schedules(connection=conn, expired=True)

# get all events
events = list_events(connection=conn)

# get single Schedule and list its properties
schedule = Schedule(connection=conn, id=SCHEDULE_ID)
schedule = Schedule(connection=conn, name=SCHEDULE_NAME)
schedule.list_properties()

# disable/enable (pass new schedule expire time)
schedule.disable()
schedule.enable(SCHEDULE_EXPIRE_TIME)

# alter schedule properties
schedule.alter(description=SCHEDULE_DESCRIPTION)

# altering schedule type is also possible;
# changing event based schedule to time based (using ScheduleTime class):
schedule.alter(time=SCHEDULE_TIME)

# Create time based schedule. Note that some parameters refer to particular time patterns and
# depend on setting recurrence_pattern or execution_pattern to respective values. In this case,
# setting daily_pattern to DAY requires specifying repeat_interval, and setting execution_pattern
# to ONCE requires specifying execution_time.
new_schedule = Schedule.create(
    connection=conn,
    name=SCHEDULE_NAME,
    schedule_type=Schedule.ScheduleType.TIME_BASED,
    start_date=SCHEDULE_START_DATE,
    recurrence_pattern=ScheduleEnums.RecurrencePattern.DAILY,
    daily_pattern=ScheduleEnums.DailyPattern.DAY,
    repeat_interval=2,
    execution_pattern=ScheduleEnums.ExecutionPattern.ONCE,
    execution_time=SCHEDULE_EXECUTE_TIME,
)
# see distribution_services/device/schedule.py for ScheduleType values
# see distribution_services/schedule/schedule_time.py for RecurrencePattern,
# DailyPattern and ExecutionPattern values

# create event based schedule
event = Event(connection=conn, name=SCHEDULE_EVENT_NAME)
new_schedule = Schedule.create(connection=conn, name=SCHEDULE_NAME,
                               schedule_type=Schedule.ScheduleType.EVENT_BASED, event_id=event.id,
                               start_date=SCHEDULE_START_DATE, stop_date=SCHEDULE_STOP_DATE)
# see distribution_services/device/schedule.py for ScheduleType values

# delete schedule
# (Note: deleting schedule will also delete related subscriptions!)
schedule.delete()

# good practice is to check if subscription is using the schedule,
# which we want to delete and if so alter it before deletion
other_schedule = Schedule(connection=conn, name=SCHEDULE_NAME)
sub1 = Subscription(connection=conn, subscription_id=SUBSCRIPTION_ID, project_name=PROJECT_NAME)
sub1.alter(schedules=other_schedule)

# get a list of subscriptions using schedule under the given project
all_subscriptions = list_subscriptions(conn, project_name=PROJECT_NAME)
subs_with_schedule = [sub for sub in all_subscriptions if sub.schedules[0].id == schedule.id]

# delete all expired schedules - user will be prompted to confirm every deletion
# (Note: deleting schedule will also delete related subscriptions!)
expired_schedules = list_schedules(connection=conn, expired=True)
for sch in expired_schedules:
    sch.delete()

# changing schedules for multiple subscriptions can be easily done using simple
# for loop (batch execution substitute)
sub2 = Subscription(connection=conn, subscription_id=SUBSCRIPTION_ID, project_name=PROJECT_NAME)
list_of_subscriptions = [sub1, sub2]
for subscription in list_of_subscriptions:
    subscription.alter(schedules=schedule)

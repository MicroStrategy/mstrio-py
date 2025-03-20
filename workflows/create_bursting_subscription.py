"""Create a bursting subscription.
1. Connect to the environment using data from workstation
2. Create a bursting configuration
   - 2.1 using objects
   - 2.2 using IDs
3. Create an email subscription with created bursting configuration
"""

from mstrio.connection import get_connection
from mstrio.distribution_services import Content, Device, EmailSubscription, Schedule
from mstrio.modeling import Attribute, AttributeForm

conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')


# Create bursting configuration, using objects
bursting = Content.Properties.Bursting(
    slicing_attributes=[Attribute(conn, id='8D679D4311D3E4981000E787EC6DE8A4')],
    address_attribute=Attribute(conn, id='8D679D4311D3E4981000E787EC6DE8A4'),
    device=Device(conn, id='1D2E6D168A7711D4BE8100B0D04B6F0B'),
    form=AttributeForm(conn, id='8A9EFEDB11D60C62C000CC8F9590594F'),
)

# Alternatively, create bursting configuration using IDs.
# However, the `slicing_attributes` should be provided in the format:
# '<attribute_id>~<attribute_name>'
# bursting = Content.Properties.Bursting(
#     slicing_attributes=['8D679D4311D3E4981000E787EC6DE8A4~Manager'],
#     address_attribute_id='8D679D4311D3E4981000E787EC6DE8A4',
#     device_id='1D2E6D168A7711D4BE8100B0D04B6F0B',
#     form_id='8A9EFEDB11D60C62C000CC8F9590594F',
# )

# Create bursting subscription
bursting_subscription = EmailSubscription.create(
    connection=conn,
    name='Bursting Subscription',
    project_name='MicroStrategy Tutorial',
    contents=[
        Content(
            id='<content_id>',  # Content should have bursting enabled
            type=Content.Type.REPORT,
            personalization=Content.Properties(
                format_type=Content.Properties.FormatType.PDF,
                bursting=bursting,
            ),
        ),
    ],
    schedules=Schedule(conn, name='Monday Morning'),
    recipients=['54F3D26011D2896560009A8E67019608'],  # Administrator
    email_subject='Bursting Subscription',
)

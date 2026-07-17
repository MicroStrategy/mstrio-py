"""
Flow Step Template: Send Email
Script Result Type: ---

This workflow template works OOTB after providing values for all required
Variables.

It represents Sending Email with custom content action.

- Content is a pure text string built from 3 components:
  - content (required)
  - content_prefix (optional), added to `content` before it
  - content_suffix (optional), added to `content` after it

It is done so in order to allow adding something before and/or after a value
which might be pre-generated. For example, `content` may be a set STDOUT of some
script in a flow and it can be beneficial to add some prefix to it, as context,
or suffix as summary.

The workflow currently assumes:
- That the connection will be established via `get_connection`
- That the email sending is done via dedicated mstrio-py method `send_email`
    utilizing REST API. Any custom setup for sending email needs to be created
    as custom script utilizing built-in `smtplib` and `email` Python libraries
    (both obsolete here)
"""

import smtplib
import email

from mstrio.connection import get_connection, Connection
from mstrio.distribution_services.email import send_email

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData)


USERS = $list_of_users_ids
SUBJECT = $subject
CONTENT = $content

if $content_prefix:
    CONTENT = $content_prefix + '\n' + CONTENT

if $content_suffix:
    CONTENT += '\n' + $content_suffix

send_email(
    conn,
    users=USERS,
    subject=SUBJECT,
    content=CONTENT,
    is_html=False,
)

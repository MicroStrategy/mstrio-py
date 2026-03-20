"""
This template shows how to create a Standard Script with return value.

When "Script Result Type" property is set, Standard Script can return a value.
- for Result Type `TEXT` you can return any string
- for Result Type `NUMERICAL` you can return a number (int or float)
- for Result Type `DATE` you can return a date or datetime string in ISO 8601 format

Below is a method required for the script to return a value shown multiple times
with different returning values. Use only one of those.
"""

# Script Result Type: TEXT
def get_results():
    return "This string will be returned from this script"

# OR

# Script Result Type: NUMERICAL
def get_results():
    return 42

# OR

# Script Result Type: DATE
def get_results():
    return "2024-01-15T10:30:00.000"

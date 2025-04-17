"""This is the demo script to show how to manage license. Its basic goal
is to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server import ContactInformation, InstallationUse, License

conn = get_connection(workstationData)

# Get license object
license = License(connection=conn)

# Print activation information
print(license.activation_info)

# Get license details
license_details = license.list_details()

# Get all license properties
license_properties = license.list_properties()

# Get all license products
license_products = license.list_products(module='all')
# Get licensed products under 'intelligence_module'
license_products_intelligence = license.list_products()
# Get licensed products under 'identity_module'
license_products_identity = license.list_products(module='identity_module')

# Print license status
print(license.status)
# Deactivate license
license.deactivate()
# Print license status
print(license.status)

# Register new license key
NEW_LICENSE_KEY = $new_license_key
license.register_new_key(NEW_LICENSE_KEY)
# Print license key
print(license.key)

# To load new license key, you need to restart the server
# After restarting the server, you can check the license key and status
print(license.key)
print(license.status)

# To activate new license key, you need to provide contact information first
# Contact information

DEPARTMENT = $department
FIRST_NAME = $first_name
LAST_NAME = $last_name
ADDRESS = $address
POSTAL = $postal
COUNTRY = $country
JOB_TITLE = $job_title
CITY = $city
PHONE = $phone
EMAIL = $email
CONFIRM_EMAIL = $confirm_email
COMPANY = $company
customer_contact_info = ContactInformation(department=DEPARTMENT,
                                            first_name=FIRST_NAME,
                                            last_name=LAST_NAME,
                                            address=ADDRESS,
                                            postal=POSTAL,
                                            country=COUNTRY,
                                            job_title=JOB_TITLE,
                                            city=CITY,
                                            phone=PHONE,
                                            email=EMAIL,
                                            confirm_email=CONFIRM_EMAIL,
                                            company=COMPANY)

LOCATION = $location

license.update_activation_request_information(location=LOCATION,
                                                installation_use=InstallationUse.PRODUCTION,
                                                customer_contact=customer_contact_info)

# Download activation xml file
ACTIVATION_XML_FILE = $activation_xml_file
license.get_activation_xml_file(save_path=ACTIVATION_XML_FILE)

# Now to obtain activation code you need to upload activation xml file into
# Strategy Licensing site and get activation code

ACTIVATION_CODE = $activation_code
# Activate license with activation code
license.activate(activation_code=ACTIVATION_CODE)
# Print activation information
print(license.activation_info)
# Print license status
print(license.status)

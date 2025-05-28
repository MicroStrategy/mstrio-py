"""This is the demo script to show how to manage license. Its basic goal
is to present what can be done with this module and to ease its usage.
"""

from time import sleep

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
# Get licensed products beginning with 'Server'
license_products_server = license.list_products(module='all', name='Server')
# Get licensed products with id 7
license_products_id_7 = license.list_products(module='all', product_id=7)

# Print license status
print(license.status)
# Deactivate license
license.deactivate()
# Print license status
print(license.status)


NEW_LICENSE_KEY = $new_license_key
# Before registering new license key, you can check its entitlements
new_entitlements = license.get_new_key_entitlements(key=NEW_LICENSE_KEY)
# Print new entitlements
print(new_entitlements)
# Register new license key
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

# License compliance check run and get
license.run_compliance_check()
# Wait for compliance check to finish
sleep(5)
# Get compliance check information
license.get_compliance_check()
# Alternatively, you can run and get compliance check in one step
license.run_and_get_compliance_check()
# Print compliance time
print(license.compliance_time)
# Print compliance result
print(license.in_compliance)
# Now you can check the compliance status for each product
print(license.list_products())

# License audit
license.run_audit()
# Wait for audit to finish
sleep(2)
# Get audit information
license.get_audit()
# Alternatively, you can run and get audit in one step
license.run_and_get_audit()
# Print audit time
print(license.audit_time)

# Export standard audit results to csv
license.export_audit_to_csv(file_path="audit_standard.csv")

# If there was a product with compliance issues, you can selectively fetch
# users' privileges for that product and export to csv semi-detailed
# audit results
for product in license.list_products(module='all'):
    if not product.in_compliance:
        product.fetch_users_privileges()
license.export_audit_to_csv(file_path="audit_semi_detailed.csv")

# Fetch all products and their users' privileges
# Depending on total number of users in the environment, this can take several
# minutes to complete
license.fetch_all_products_users_privileges()
# Export detailed audit results to csv
license.export_audit_to_csv(file_path="audit_detailed.csv")

# Export to .json
license.export_audit_to_dataframe(file_path = "detailed_audit.json")

# Export to .pkl
license.export_audit_to_dataframe(file_path = "detailed_audit.pkl")

# Export to df
df = license.export_audit_to_dataframe()
print(df.head())

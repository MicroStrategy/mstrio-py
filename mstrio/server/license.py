import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import auto
from time import sleep
from typing import TYPE_CHECKING

import humps
import pandas as pd

from mstrio import config
from mstrio.api import license as license_api
from mstrio.connection import Connection
from mstrio.server import Environment
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import (
    Dictable,
    IServerError,
    camel_to_snake,
    key_fn_for_sort_object_properties,
)
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.access_and_security import Privilege

logger = logging.getLogger(__name__)
WS_TIME_FORMAT = '%Y-%m-%d %I:%M:%S %p'


class InstallationUse(AutoName):
    """Enumeration constant indicating installation use"""

    DEVELOPMENT = auto()
    TESTING = auto()
    PRODUCTION = auto()
    TRAINING = auto()
    OTHER = auto()


@dataclass
class ContactInformation(Dictable):
    """Contact information for license management. This class represents
    contact information required for license operations.
    """

    department: str
    first_name: str
    last_name: str
    job_title: str
    phone: str
    email: str
    confirm_email: str
    address: str
    city: str
    postal: str
    country: str
    company: str
    use_personal_info: bool = False
    state: str | None = None

    def __post_init__(self):
        if self.email != self.confirm_email:
            raise ValueError("Email address and confirmation email do not match")


@dataclass
class ActivationInfo(Dictable):
    """Class that represents license activation information. It contains details
    about the activation status, activation and deactivation codes, and other
    related information.
    """

    activated: bool
    activation_count: int
    activation_needed: bool
    user_provided_info: dict | None = None
    activation_code: str | None = None
    deactivation_code: str | None = None
    activation_date: str | None = None


@dataclass
class MachineInfo(Dictable):
    """
    Class representing system hardware and operating system information
    for a machine.

    """

    cpu_speed: str
    cpu_type: str
    OS: str
    host_id: str
    kernel_release: str
    machine_name: str
    num_physical_cpus: int
    system_language: str


@dataclass
class PrivilegeInfo(Dictable):
    """Class representing a privilege information in the license management
    system.
    """

    privilege: "Privilege"
    sources: list[str] | None = None


@dataclass
class UserLicense(Dictable):
    """Class representing a user license in the license management system."""

    id: str
    name: str
    enabled: bool
    date_created: str
    date_modified: str
    ldap: bool | None = None
    privileges: list[PrivilegeInfo] | None = None


@dataclass
class Product(Dictable):
    """Class encapsulating details about a licensed product within the Strategy
    ecosystem.
    """

    count: int
    duration: int
    id: int
    name: str
    period: int
    type: str
    module: str
    _connection: Connection
    in_compliance: bool | None = None
    license_in_use: int | None = None
    users: list[UserLicense] | None = None

    PRODUCT_NAME_MAP = {
        0: "RESERVED",
        6: "SERVER_REPORTER",
        17: "GATEWAY_EMM_AIRWATCH_BY_VMWARE",
        23: "CLIENT_APPLICATION_OFFICE",
        30: "CLIENT_HYPER_API",
        32: "PLACEHOLDER_1",
        33: "PLACEHOLDER_2",
        34: "CLIENT_APPLICATION_RSTUDIO",
        35: "PRODUCT_01",
        36: "PRODUCT_02",
        37: "PRODUCT_03",
        38: "PRODUCT_04",
        39: "PRODUCT_05",
        40: "PRODUCT_06",
    }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"type='{self.type}', "
            f"license_in_use='{self.license_in_use}', "
            f"Entitlements count='{self.count}', "
            f"in_compliance='{self.in_compliance}')"
        )

    def fetch_users_privileges(self) -> None:
        """Fetch users privileges for the product."""
        from mstrio.access_and_security import Privilege

        if self.users:
            for user in self.users:
                user_privileges = camel_to_snake(
                    license_api.get_privileges_for_user(
                        connection=self._connection,
                        id=user.id,
                        license_product=self._convert_product_name_to_constant_format(),
                    ).json()
                ).get('pws')
                for record in user_privileges:
                    priv_obj = Privilege.from_dict(
                        record.get('privilege'), self._connection
                    )

                    privilege_info = PrivilegeInfo(priv_obj, record.get('sources'))
                    user.privileges.append(privilege_info)

    def _convert_product_name_to_constant_format(self) -> str:
        if self.id in self.PRODUCT_NAME_MAP:
            return self.PRODUCT_NAME_MAP[self.id]
        first_step = self.name.replace("-", "").replace(" ", "")
        result = humps.decamelize(first_step)
        return result.upper()


@dataclass
class Record(Dictable):
    """Class representing a record in the license management history"""

    activity: str
    build: str
    code: str
    contract_id: str
    issue_date: str
    key: str
    key_group: str
    products_install: list
    products_repair: list
    products_uninstall: list
    products_update: list
    release: str
    source: str
    state: str
    time: str

    def __repr__(self) -> str:
        time = datetime.strptime(self.time, '%Y-%m-%dT%H:%M:%SZ')
        formatted_time = time.strftime(WS_TIME_FORMAT)
        return (
            f"{self.__class__.__name__}("
            f"time='{formatted_time}', "
            f"activity='{self.activity}', "
            f"source='{self.source}', "
            f"state='{self.state}')"
        )


@class_version_handler('11.3.1200')
class License(Dictable):
    """License class for Strategy license management.

    This class provides functionality to manage Strategy licenses, including:
    - Retrieving license information
    - Registering new license keys
    - Activating and deactivating licenses
    - Managing activation requests
    - Generating and downloading activation XML files

    Attributes:
        bypass_audit (bool): Flag indicating if audit functionality is bypassed.
        bypass_cpu_controls (bool): Flag indicating if CPU controls are
            bypassed.
        contract_id (str): The contract ID of the license.
        disable_activation (bool): Flag indicating if activation is disabled.
        enable_daily_report (bool): Flag indicating if daily reporting is
            enabled.
        enable_key_level_evaluation (bool): Flag for key level evaluation.
        installation_version (str): Version of the installation.
        internal (bool): Flag indicating if the license is internal.
        issue_date (str): Date when the license was issued.
        license_key_group (str): License key group information.
        machine_info (MachineInfo): Information about the machine where license
            is installed.
        platform (str): Platform information for the license.
        pre_release (bool): Flag indicating if it's a pre-release version.
        products (list): List of products included in the license.
        register_date (str): Date when the license was registered.
        registration_disabled (bool): Flag indicating if registration is
            disabled.
        status (str): Current status of the license.
        edition (str): Edition of the license.
        cpu_allowance (int): CPU allowance for the license.
        AWS (bool): Flag indicating if it's an AWS installation.
        act_aware_products (list): List of activation aware products.
        DSI (bool): Flag indicating if DSI is enabled.
        installation_type (str): Type of installation.
        enabled_poc (bool): Flag indicating if PoC is enabled.
        key (str): License key.
        v_cpus (int): Number of virtual CPUs.
        activation_info (ActivationInfo): Information about license activation.
        compliance_time (str): Time of the last compliance check.
        compliance_type (str): Type of the last compliance check.
        in_compliance (bool): Flag indicating if the license is in compliance.
        compliance_running (bool): Flag indicating if compliance check is
            currently running.
        audit_time (str): Time of the last audit.
    """

    FIELDNAMES = [
        "Product",
        "User Full Name",
        "User ID",
        "User State",
        "Creation Date (User)",
        "Last Modified (User)",
        "LDAP (User)",
        "Privilege Name",
        "Privilege ID",
        "Inherited from User Group",
        "Inherited from Security Role",
        "Project",
    ]

    def __init__(self, connection: Connection, node_name: str | None = None):
        """Initialize License object.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            node_name (str, optional): Name of the node to get license
                information from. On the one node environment can be None.
        """
        self._connection = connection
        self._node_name = None
        self._activation_info = None
        self._compliance_time = None
        self._compliance_type = None
        self._in_compliance = None
        self._compliance_running = None
        self._audit_time = None
        self._check_node_name(node_name)
        resp = license_api.get_license(
            connection=self._connection, node_name=self._node_name
        )
        retr = camel_to_snake(resp.json())
        self._init_variables(**retr)
        if config.verbose:
            logger.info(
                f"License object successfully initialized for node '{self._node_name}'."
            )

    def _init_variables(self, **kwargs) -> None:
        """This function initializes variables using keyword arguments
        passed to it.
        """
        if kwargs.get('machine_info'):
            physical_cpus = kwargs['machine_info'].get('num_physical_cp_us')
            kwargs['machine_info']['num_physical_cpus'] = physical_cpus
            del kwargs['machine_info']['num_physical_cp_us']

        self.bypass_audit = kwargs.get('bypass_audit')
        self.bypass_cpu_controls = kwargs.get('bypass_cpu_controls')
        self.contract_id = kwargs.get('contract_id')
        self.disable_activation = kwargs.get('disable_activation')
        self.enable_daily_report = kwargs.get('enable_daily_report')
        self.enable_key_level_evaluation = kwargs.get('enable_key_level_evaluation')
        self.installation_version = kwargs.get('installation_version')
        self.internal = kwargs.get('internal')
        self.issue_date = kwargs.get('issue_date')
        self.license_key_group = kwargs.get('license_key_group')
        self.machine_info = (
            MachineInfo(**kwargs['machine_info'])
            if kwargs.get('machine_info')
            else None
        )
        self.platform = kwargs.get('platform')
        self.pre_release = kwargs.get('pre_release')
        self.products = [
            Product(module=key, _connection=self._connection, **product_info)
            for key, products_list in kwargs.get('products', {}).items()
            for product_info in products_list
        ]
        self.register_date = kwargs.get('register_date')
        self.registration_disabled = kwargs.get('registration_disabled')
        self.status = kwargs.get('status')
        self.edition = kwargs.get('edition')
        self.cpu_allowance = kwargs.get('cpu_allowance')
        self.AWS = kwargs.get('AWS')
        self.act_aware_products = kwargs.get('act_aware_products')
        self.DSI = kwargs.get('DSI')
        self.installation_type = kwargs.get('installation_type')
        self.enabled_poc = kwargs.get('enabled_poc')
        self.key = kwargs.get('key')
        self.v_cpus = kwargs.get('v_cp_us')

    def register_new_key(self, key: str) -> None:
        """Register a new license key. After registering a new key, the server
        must be restarted to apply the changes.

        Args:
            key (str): License key to register.
        """
        operations_list = [
            {
                "op": "replace",
                "path": "/key",
                "value": key,
            }
        ]
        license_api.update_license_information(
            self._connection, self._node_name, operations_list
        )
        if config.verbose:
            logger.info(
                "License key registered successfully. Now please restart the "
                "I-Server to apply the changes."
            )
        self._fetch()

    def activate(self, activation_code: str) -> None:
        """Activate the license.

        Args:
            activation_code: Activation code. To obtain the activation code you
                need to upload xml activation file on the Strategy licensing
                site.
        """
        operations_list = [
            {
                "op": "add",
                "path": "/activationCode",
                "value": activation_code,
            },
            {"op": "replace", "path": "/activated", "value": True},
        ]
        license_api.update_license_activation(
            self._connection, self._node_name, operations_list
        )
        if config.verbose:
            logger.info("License activated successfully.")
        self._fetch()

    def deactivate(self) -> None:
        """Deactivate the license."""
        operations_list = [{"op": "replace", "path": "/activated", "value": False}]
        license_api.update_license_activation(
            self._connection, self._node_name, operations_list
        )
        if config.verbose:
            logger.info("License deactivated successfully.")
        self._fetch()

    def list_details(self) -> dict:
        """Return a dictionary with license details.

        Returns:
            Dictionary with license details excluding products information.
        """
        attributes = {
            key: self.__dict__[key]
            for key in self.__dict__
            if not key.startswith('_') and key != 'products'
        }

        return {
            key: attributes[key]
            for key in sorted(attributes, key=key_fn_for_sort_object_properties)
        }

    def list_products(
        self,
        module: str = 'intelligence_module',
        product_id: int | list[int] | None = None,
        name: str | None = None,
    ) -> list:
        """Return a list of licensed products.
        Args:
            module (str, optional): Module name to filter products list.
                Default is 'intelligence_module', input 'all' to get list of
                products in every module.
            product_id (int | list[int], optional): Product IDs to filter
                products list. If provided, it should be a single ID or a list
                of IDs.
            name (str, optional): Product name to filter products list.
        Returns:
            List of licensed products.

        """
        if product_id is not None and name:
            raise ValueError(
                "You can provide either 'id' or 'name' to filter products, not both."
            )
        products = None
        if module == 'all':
            products = self.products
        else:
            if not any(product.module == module for product in self.products):
                raise ValueError(
                    f"Module '{module}' not found. Available modules: "
                    f"{', '.join({product.module for product in self.products})}"
                )
            products = [
                product for product in self.products if product.module == module
            ]
        if product_id is not None:
            if isinstance(product_id, int):
                product_id = [product_id]
            products = [product for product in products if product.id in product_id]
        if name:
            products = [
                product for product in products if name.lower() in product.name.lower()
            ]
        return sorted(products, key=lambda x: x.name)

    def list_properties(self) -> dict:
        """Return a dictionary with all license properties.

        Returns:
            Dictionary with all license properties.
        """
        attributes = {
            key: self.__dict__[key] for key in self.__dict__ if not key.startswith('_')
        }
        attributes = {
            **attributes,
            'connection_url': self._connection.base_url,
            'node_name': self._node_name,
            'activation_info': self.activation_info,
        }

        return {
            key: attributes[key]
            for key in sorted(attributes, key=key_fn_for_sort_object_properties)
        }

    def fetch(self) -> None:
        """Fetch the current license information from the environment."""
        self._fetch()
        if config.verbose:
            logger.info("License information fetched successfully.")

    def update_activation_request_information(
        self,
        location: str,
        installation_use: InstallationUse,
        customer_contact: ContactInformation | dict | str,
        employee_of_licensed_company: bool = True,
        installer_contact: ContactInformation | dict | str | None = None,
    ) -> None:
        """Update activation request information for the license.

        Args:
            location (str): Physical location of the installation.
            installation_use (InstallationUse) : Purpose of the installation
                (development, testing, production, training, or other).
            customer_contact (ContactInformation | dict | str): Contact
                information of the customer. Can be a ContactInformation object,
                dictionary or path to a file (JSON or CSV).
            employee_of_licensed_company (bool): Whether the person performing
                installation is an employee of licensed company or not.
                If False, installer_contact must be provided.
            installer_contact (ContactInformation | dict | str, optional):
                Contact information of the installer. Can be a
                ContactInformation object, dictionary or path to a file (JSON
                or CSV). Required when employee_of_licensed_company is False.
        """
        operations_list = [
            {
                "op": "add",
                "path": "/userProvidedInfo",
                "value": {
                    "installationName": self._node_name,
                    "installationLocation": location,
                    "installationUse": installation_use.value,
                    "contact": {},
                },
            }
        ]
        self._prepare_body_for_information_update(
            operations_list, customer_contact, 'customer'
        )
        if not employee_of_licensed_company:
            if not installer_contact:
                raise ValueError(
                    "Installer contact information is required when you are not an "
                    "employee of licensed company."
                )
            self._prepare_body_for_information_update(
                operations_list, installer_contact, 'installer'
            )
        else:
            operations_list[0]['value']['contact']['customer'][
                'company'
            ] = 'MicroStrategy'
        license_api.update_license_activation(
            self._connection, self._node_name, operations_list
        )
        if config.verbose:
            logger.info(
                "Activation request information updated successfully. "
                "Now you can download the activation XML file."
            )

        self.get_activation_info()

    def get_activation_xml_file(self, save_path: str) -> None:
        """Get the activation XML file to upload to the Strategy licensing site.

        Args:
            save_path (str): Path where the XML file will be saved.
                Must end with '.xml'.

        Raises:
            ValueError: If save_path doesn't end with '.xml' or if there's an
                error saving the file.
        """
        resp = license_api.get_activation_xml_file(self._connection, self._node_name)
        if not save_path.lower().endswith('.xml'):
            raise ValueError(
                "Save path must end with '.xml'. Please provide a valid file path."
            )
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(resp.json())
        except Exception as e:
            raise ValueError(f"Error saving activation XML file: {str(e)}")
        if config.verbose:
            logger.info(
                f"Activation XML file saved successfully to '{save_path}'. "
                "Please upload it to Strategy licensing site."
            )

    def get_activation_info(self) -> ActivationInfo:
        """Get information about the license activation.

        Returns:
            ActivationInfo object with license activation details.
        """
        resp = license_api.get_license_activation_info(
            connection=self._connection, node_name=self._node_name
        )
        self._activation_info = ActivationInfo.from_dict(resp.json())
        return self._activation_info

    def get_history(self) -> list[Record]:
        """Get the license history.

        Returns:
            List of Record objects representing the license history.
        """
        resp = license_api.get_license_history(
            connection=self._connection, node_name=self._node_name
        )
        history = resp.json().get('activities', [])
        return sorted(
            (Record.from_dict(record) for record in history),
            key=lambda x: x.time,
        )

    def run_compliance_check(self) -> None:
        """Run a compliance check on the license."""
        license_api.run_compliance_check(connection=self._connection)
        if config.verbose:
            logger.info("Compliance check request sent successfully.")

    def get_compliance_check(self) -> None:
        """Get the compliance check details."""
        resp = camel_to_snake(
            license_api.get_compliance_check(connection=self._connection).json()
        )
        self._compliance_time = resp.get('compliance_time')
        self._compliance_type = resp.get('compliance_type')
        self._in_compliance = resp.get('in_compliance')
        if self._compliance_time:
            self._compliance_time = datetime.strptime(
                self._compliance_time, '%Y-%m-%dT%H:%M:%S.%fZ'
            ).strftime(WS_TIME_FORMAT)
        for elem in resp.get('compliance_result', []):
            product = list(
                filter(
                    lambda x, current_elem=elem: x.id == current_elem.get('type'),
                    self.products,
                )
            )
            for found_product in product:
                found_product.in_compliance = elem.get('inCompliance')
                found_product.license_in_use = elem.get('currentUsage')
        if (
            self._compliance_type == 0
            and self._compliance_time is None
            and self._in_compliance is False
        ):
            logger.warning(
                'Compliance check is unavailable when license key contains '
                'mixed license types for several products.'
            )
        if config.verbose:
            logger.info("Compliance check results fetched successfully.")

    def get_compliance_check_status(self) -> None:
        """Get the compliance check status."""
        resp = license_api.get_compliance_check_status(connection=self._connection)
        self._compliance_running = resp.json().get('jobRunning')

    def run_and_get_compliance_check(
        self, timeout: int = 30, retry_interval: int = 1
    ) -> None:
        """Run a compliance check and get the results with a timeout.

        Args:
            timeout (int, optional): Maximum time (in seconds) to wait for
                compliance check to complete.
            retry_interval (int, optional): Time interval (in seconds) between
                retries.
        """
        initial_compliance_time = self.compliance_time
        self.run_compliance_check()
        start_time = datetime.now()

        # Wait for compliance check status to change to not running
        while (
            self.compliance_running
            and (datetime.now() - start_time).total_seconds() < timeout
        ):
            sleep(retry_interval)
            self.get_compliance_check_status()

        if self.compliance_running:
            raise TimeoutError(
                "Compliance check did not complete within the allowed timeout."
            )

        # Fetch results and wait for compliance_time to update
        while (
            self.compliance_time == initial_compliance_time
            and (datetime.now() - start_time).total_seconds() < timeout
        ):
            sleep(retry_interval)
            self.get_compliance_check()

        if self.compliance_time == initial_compliance_time:
            raise TimeoutError(
                "Compliance check results were not updated within the allowed timeout."
            )

    def run_audit(self) -> dict:
        """Run a license audit.
        Returns:
            dict: Dictionary about the audit request.
        """
        resp = license_api.run_audit(connection=self._connection)
        if config.verbose:
            logger.info("License audit request sent successfully.")
        return camel_to_snake(resp.json())

    def get_audit(self) -> None:
        """Get the audit results."""
        resp = camel_to_snake(license_api.get_audit(connection=self._connection).json())
        self._audit_time = resp.get('audit_time')
        if self._audit_time:
            self._audit_time = datetime.strptime(
                self._audit_time, '%Y-%m-%dT%H:%M:%S.%fZ'
            ).strftime(WS_TIME_FORMAT)

        product_map = {product.id: product for product in self.products}
        for product in self.products:
            product.users = []

        for elem in resp.get('user_licenses', []):
            user_license = UserLicense(
                id=elem.get('id'),
                name=elem.get('name'),
                enabled=elem.get('enabled'),
                date_created=elem.get('creationTime'),
                date_modified=elem.get('modificationTime'),
                ldap=elem.get('LDAPUser'),
                privileges=[],
            )
            for product_id in elem.get('licenseTypes', []):
                if product := product_map.get(product_id):
                    product.users.append(user_license)
        if config.verbose:
            logger.info("License audit results fetched successfully.")

    def run_and_get_audit(self, timeout: int = 30, retry_interval: int = 1) -> None:
        """Run a license audit and get the results with a timeout.

        Args:
            timeout (int, optional): Maximum time (in seconds) to wait for
                the audit to complete.
            retry_interval (int, optional): Time interval (in seconds) between
                retries.
        """
        initial_audit_time = self.audit_time
        self.run_audit()
        start_time = datetime.now()

        # Wait for audit time to update
        while (
            self.audit_time == initial_audit_time
            and (datetime.now() - start_time).total_seconds() < timeout
        ):
            sleep(retry_interval)
            self.get_audit()

        if self.audit_time == initial_audit_time:
            raise TimeoutError(
                "Audit results were not updated within the allowed timeout."
            )

    def fetch_all_products_users_privileges(self) -> None:
        """Fetch all products and their users' privileges."""
        if not self._audit_time:
            self.get_audit()
        for product in self.products:
            try:
                product.fetch_users_privileges()
            except IServerError as e:
                logger.error(
                    "Error fetching user privileges for product '%s': %s",
                    product.name,
                    e,
                )
        if config.verbose:
            logger.info(
                "All products and their users' privileges fetched successfully."
            )

    def get_new_key_entitlements(self, key: str) -> dict:
        """Get the entitlements for a new license key.

        Args:
            key (str): License key to get entitlements for.

        Returns:
            dict: Dictionary with the entitlements for the new license key.
        """
        resp = license_api.get_license_entitlements(
            connection=self._connection, node_name=self._node_name, license_key=key
        )
        return resp.json()

    def export_audit_to_csv(self, file_path: str) -> pd.DataFrame:
        """Export the audit results to a CSV file.

        IMPORTANT: To export detailed audit results, you need to fetch all
        products and their users' privileges first using the
        `fetch_all_products_users_privileges` method.

        Args:
            file_path (str): Path to the CSV file where the audit results will
                be saved.
        Returns:
            pd.DataFrame: DataFrame containing the audit results.
                In case of detailed audit results, if privilege is granted
                directly to the user, the columns 'Inherited from User Group',
                'Inherited from Security Role' and 'Project' will be set to
                '--'.
                If privilege is inherited from a UserGroup, the column
                'Inherited from User Group' will be set to the name of the
                UserGroup, columns 'Inherited from Security Role' and 'Project'
                will be set to '--'.
                If privilege is inherited from a SecurityRole, the column
                'Inherited from User Group' will be set to '--', columns
                'Inherited from Security Role' will be set to the name of the
                SecurityRole and 'Project' will be set to the name of the
                project the SecurityRole is assigned to.
        """
        if not file_path.lower().endswith('.csv'):
            raise ValueError("File path must end with '.csv'.")
        df = self.export_audit_to_dataframe(file_path)
        return df

    def export_audit_to_dataframe(self, file_path: str | None = None) -> pd.DataFrame:
        """Create and return a DataFrame containing the audit results.
        Optionally, save the DataFrame to a file.

        IMPORTANT: To export detailed audit results, you need to fetch all
        products and their users' privileges first using the
        `fetch_all_products_users_privileges` method.

        Args:
            file_path (str, optional): Path to the file where the DataFrame
                will be saved. If None, the DataFrame will not be saved. It
                can be a path to a .pkl, .json or .csv file.
        Returns:
            pd.DataFrame: DataFrame containing the audit results.
                In case of detailed audit results, if privilege is granted
                directly to the user, the columns 'Inherited from User Group',
                'Inherited from Security Role' and 'Project' will be set to
                '--'.
                If privilege is inherited from a UserGroup, the column
                'Inherited from User Group' will be set to the name of the
                UserGroup, columns 'Inherited from Security Role' and 'Project'
                will be set to '--'.
                If privilege is inherited from a SecurityRole, the column
                'Inherited from User Group' will be set to '--', columns
                'Inherited from Security Role' will be set to the name of the
                SecurityRole and 'Project' will be set to the name of the
                project the SecurityRole is assigned to.
        """

        rows = self._generate_audit_data()
        df = pd.DataFrame(rows, columns=self.FIELDNAMES)
        if file_path:
            if file_path.lower().endswith('.pkl'):
                df.to_pickle(file_path)
            elif file_path.lower().endswith('.json'):
                df.to_json(file_path, orient='records', lines=True)
            elif file_path.lower().endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8')
            else:
                raise ValueError("File path must end with '.pkl', '.json' or '.csv'.")
            if config.verbose:
                logger.info(f"Audit results exported successfully to '{file_path}'.")
        return df

    def _generate_audit_data(self) -> list[dict]:
        """Generate audit data as a list of dictionaries."""
        if not self.audit_time:
            self.get_audit()

        rows = []
        for product in self.products:
            for user in product.users:
                if user.privileges:
                    rows.extend(self._generate_rows_for_user_privileges(product, user))
                else:
                    rows.append(self._build_na_record(product, user))
        return rows

    def _generate_rows_for_user_privileges(
        self, product: Product, user: UserLicense
    ) -> list[dict]:
        """Generate rows for user privileges."""
        rows = []
        for privilege_record in user.privileges:
            for source in privilege_record.sources:
                user_group, security_role, project = self._define_source(source)
                rows.append(
                    {
                        self.FIELDNAMES[0]: product.name,
                        self.FIELDNAMES[1]: user.name,
                        self.FIELDNAMES[2]: user.id,
                        self.FIELDNAMES[3]: "Enabled" if user.enabled else "Disabled",
                        self.FIELDNAMES[4]: user.date_created,
                        self.FIELDNAMES[5]: user.date_modified,
                        self.FIELDNAMES[6]: user.ldap,
                        self.FIELDNAMES[7]: privilege_record.privilege.name,
                        self.FIELDNAMES[8]: privilege_record.privilege.id,
                        self.FIELDNAMES[9]: user_group,
                        self.FIELDNAMES[10]: security_role,
                        self.FIELDNAMES[11]: project,
                    }
                )
        return rows

    def _build_na_record(self, product: Product, user: UserLicense) -> dict:
        """
        Build a record with N/A placeholders when privileges aren't present.
        """
        return {
            self.FIELDNAMES[0]: product.name,
            self.FIELDNAMES[1]: user.name,
            self.FIELDNAMES[2]: user.id,
            self.FIELDNAMES[3]: "Enabled" if user.enabled else "Disabled",
            self.FIELDNAMES[4]: user.date_created,
            self.FIELDNAMES[5]: user.date_modified,
            self.FIELDNAMES[6]: user.ldap,
            self.FIELDNAMES[7]: "N/A",
            self.FIELDNAMES[8]: "N/A",
            self.FIELDNAMES[9]: "N/A",
            self.FIELDNAMES[10]: "N/A",
            self.FIELDNAMES[11]: "N/A",
        }

    def _define_source(self, source: dict) -> tuple[str, str, str]:
        """Define the source of the license.

        Args:
            source (dict): Dictionary containing source information.

        Returns:
            tuple[str, str, str]: A tuple containing the UserGroup, SecurityRole
                and Project information.
        """
        security_role = 'N/A'
        user_group = 'N/A'
        project = 'N/A'

        # Record points that this privilege is directly assigned to the user
        if source.get('direct'):
            security_role = '--'
            user_group = '--'
            project = '--'
        else:
            # Record points that this privilege is inherited from a UserGroup
            if from_group := source.get('group'):
                security_role = '--'
                user_group = from_group.get('name', '--')
                project = '--'
            # Record points that this privilege is inherited from a SecurityRole
            if from_role := source.get('securityRole'):
                security_role = from_role.get('name', '--')
                user_group = '--'
                if on_project := source.get('project'):
                    project = on_project.get('name', '--')
        return user_group, security_role, project

    def _fetch(self) -> None:
        resp = license_api.get_license(
            connection=self._connection, node_name=self._node_name
        )
        retr = camel_to_snake(resp.json())
        self._init_variables(**retr)
        self.get_activation_info()

    def _read_contact_information_from_file(self, file_path: str) -> dict:
        """Read contact information from JSON or CSV files.

        Args:
            file_path (str): Path to the JSON or CSV file containing contact
                information.

        Returns:
            Dictionary with the read contact information.

        Raises:
            ValueError: If the file extension is not supported or if there's an
                error parsing the file.
        """

        file_ext = file_path.lower().split('.')[-1]

        try:
            if file_ext == 'json':
                with open(file_path) as f:
                    return json.load(f)
            if file_ext == 'csv':
                with open(file_path, newline='') as f:
                    reader = csv.DictReader(f)
                    data = next(reader)
                    for key, value in data.items():
                        if isinstance(value, str) and value.lower() in [
                            'true',
                            'false',
                        ]:
                            data[key] = value.lower() == 'true'
                    return data
            raise ValueError(
                f"Unsupported file extension: {file_ext}. Use .json or .csv files."
            )
        except Exception as e:
            raise ValueError(f"Error reading contact information from file: {str(e)}")

    def _prepare_body_for_information_update(
        self,
        operations_list: list,
        information: ContactInformation | dict | str,
        contact_key: str,
    ) -> None:
        if isinstance(information, ContactInformation):
            operations_list[0]['value']['contact'][contact_key] = information.to_dict()
        elif isinstance(information, dict):
            operations_list[0]['value']['contact'][contact_key] = information
        else:
            operations_list[0]['value']['contact'][contact_key] = (
                self._read_contact_information_from_file(information)
            )
        if 'confirmEmail' in operations_list[0]['value']['contact'][contact_key]:
            del operations_list[0]['value']['contact'][contact_key]['confirmEmail']

    def _check_node_name(self, node_name: str | None = None) -> None:
        """Check if the provided node name is valid and set the node name
        property.

        Args:
            node_name: Name of the node to check. If None, the first node
                will be used and assigned to node_name property.

        Raises:
            ValueError: If the node name is not found or if multiple nodes exist
                 but none specified.
        """
        env = Environment(connection=self._connection)
        nodes = env.nodes
        if node_name:
            if not any(node['name'] == node_name for node in nodes):
                raise ValueError(f"Node '{node_name}' not found in the environment.")
        else:
            if len(nodes) > 1:
                possible_nodes = [node['name'] for node in nodes]
                raise ValueError(
                    "Multiple nodes found in the environment. Please specify "
                    f"the node name. Possible nodes: {possible_nodes}"
                )
        self._node_name = node_name or nodes[0]['name']

    @property
    def activation_info(self) -> ActivationInfo:
        """ActivationInfo object with license activation details."""
        if not self._activation_info:
            self.get_activation_info()
        return self._activation_info

    @property
    def compliance_time(self) -> str:
        """Time of the last compliance check."""
        if not self._compliance_time:
            self.get_compliance_check()
        return self._compliance_time

    @property
    def compliance_type(self) -> int:
        """Type of the last compliance check."""
        if not self._compliance_type:
            self.get_compliance_check()
        return self._compliance_type

    @property
    def in_compliance(self) -> bool:
        """Whether the license is in compliance or not."""
        if self._in_compliance is None:
            self.get_compliance_check()
        return self._in_compliance

    @property
    def compliance_running(self) -> str:
        """Compliance check status of the license."""
        if not self._compliance_running:
            self.get_compliance_check_status()
        return self._compliance_running

    @property
    def audit_time(self) -> str:
        """Time of the last audit."""
        if not self._audit_time:
            self.get_audit()
        return self._audit_time

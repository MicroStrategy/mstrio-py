import csv
import json
import logging

from dataclasses import dataclass
from enum import auto

from mstrio import config
from mstrio.api import license as license_api
from mstrio.connection import Connection
from mstrio.server import Environment
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, camel_to_snake, sort_object_properties
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


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
class Product:
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
    """

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
            Product(module=key, **product_info)
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
            for key in sorted(attributes, key=sort_object_properties)
        }

    def list_products(self, module: str = 'intelligence_module') -> list:
        """Return a list of licensed products.
        Args:
            module (str, optional): Module name to filter products list.
                Default is 'intelligence_module', input 'all' to get list of
                products in every module.
        Returns:
            List of licensed products.

        """
        if module == 'all':
            return self.products
        else:
            if not any(product.module == module for product in self.products):
                raise ValueError(
                    f"Module '{module}' not found. Available modules: "
                    f"{', '.join(set(product.module for product in self.products))}"
                )
            return [product for product in self.products if product.module == module]

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
            for key in sorted(attributes, key=sort_object_properties)
        }

    def fetch(self) -> None:
        """Fetch the current license information from the environment."""
        self._fetch()
        if config.verbose:
            logger.info("License information fetched successfully.")

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
                with open(file_path, 'r') as f:
                    return json.load(f)
            if file_ext == 'csv':
                with open(file_path, 'r', newline='') as f:
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
                raise ValueError(
                    "Multiple nodes found in the environment. Please specify "
                    "the node name."
                )
        self._node_name = node_name or nodes[0]['name']

    @property
    def activation_info(self) -> ActivationInfo:
        """ActivationInfo object with license activation details."""
        if not self._activation_info:
            self.get_activation_info()
        return self._activation_info

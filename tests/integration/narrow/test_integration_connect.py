import time
import unittest
from io import StringIO
from unittest.mock import patch

import pandas as pd

from ..resources import mstr_connect as con
from ..resources import mstr_import as imp
from ..resources.commons import read_configs


class TestConnect(unittest.TestCase):
    def setUp(self):
        general_config_path = "production/tests/resources/general_configs2.json"
        additional_configs_path = (
            "production/tests/resources/additional_connection_configs.json"
        )
        general_configs = read_configs(general_config_path)
        additional_configs = read_configs(additional_configs_path)

        self.url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.project_id = general_configs["project_id"]
        self.cube_id = general_configs["dataset_ids"]["basic_cube"]
        self.proxies = general_configs["proxies"]

        self.username_no_prvlg = additional_configs["username_no_prvlg"]
        self.password_no_prvlg = additional_configs["password_no_prvlg"]
        self.base_url_no_prvlg = additional_configs["base_url_no_prvlg"]
        self.project_id_no_prvlg = additional_configs["project_id_no_prvlg"]
        self.login_mode_no_prvlg = additional_configs["login_mode_no_prvlg"]

        self.username_no_supp = additional_configs["username_no_supp"]
        self.password_no_supp = additional_configs["password_no_supp"]
        self.base_url_no_supp = additional_configs["base_url_no_supp"]
        self.project_id_no_supp = additional_configs["project_id_no_supp"]
        self.login_mode_no_supp = additional_configs["login_mode_no_supp"]

        self.attribute_ids = self.get_ids(general_configs, "attributes", "basic_cube")
        self.metric_ids = self.get_ids(general_configs, "metrics", "basic_cube")
        self.element_ids = self.get_ids(general_configs, "elements", "basic_cube")
        self.ssl_verify = True

    def test_get_connection(self):
        """TC62864"""
        connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=self.project_id,
        )
        connection.connect()

        self.assertEqual(connection.username, self.username)
        self.assertEqual(connection.password, self.password)
        self.assertEqual(connection.login_mode, self.login_mode)
        self.assertEqual(connection.session.verify, self.ssl_verify)
        self.assertIsNotNone(connection.session.headers["X-MSTR-AuthToken"])

        # NOTE: connection object executes connect() method during initialization
        #       next run of connect() method renews connection
        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.connect()
            self.assertGreater(len(mock_output.getvalue()), 1)

    def test_connection_status(self):
        """TC62858"""
        connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=self.project_id,
        )
        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.status()
            self.assertGreater(len(mock_output.getvalue()), 1)

    def test_renewing_connection(self):
        """TC62861"""
        connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=self.project_id,
        )

        self.assertIsNotNone(connection.session.headers["X-MSTR-AuthToken"])
        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.renew()
            self.assertGreater(len(mock_output.getvalue()), 1)

    def test_closing_connection(self):
        """TC62863"""
        connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=self.project_id,
        )

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.close()
            self.assertGreater(len(mock_output.getvalue()), 1)

    def test_connection_e2e(self):
        """TC62856"""
        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection = con.get_connection(
                url=self.url,
                username=self.username,
                password=self.password,
                login_mode=self.login_mode,
                project_id=self.project_id,
            )
            connection.connect()
            connection.renew()
            connection.status()
            connection.close()
            self.assertEqual(len(mock_output.getvalue().split("\n")), 6)

    def test_create_check_import_renew_e2e(self):
        """TC62860"""
        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection = con.get_connection(
                url=self.url,
                username=self.username,
                password=self.password,
                login_mode=self.login_mode,
                project_id=self.project_id,
            )
            connection.connect()
            connection.status()
            cube = imp.get_cube_dataframe(
                connection=connection,
                cube_id=self.cube_id,
                attribute_filter=self.attribute_ids,
                metric_filter=self.metric_ids,
                element_filter=self.element_ids,
            )
            self.assertIsInstance(cube, pd.DataFrame)
            time.sleep(1)
            connection.renew()
            cube = imp.get_cube_dataframe(
                connection=connection,
                cube_id=self.cube_id,
                attribute_filter=self.attribute_ids,
                metric_filter=self.metric_ids,
                element_filter=self.element_ids,
            )

            connection.close()
            self.assertEqual(len(mock_output.getvalue().split("\n")), 6)

    def test_connection_full(self):
        """TC65906"""

        CONNECTION_CONNECT_RENEWED = (
            "Connection to MicroStrategy Intelligence Server was renewed.\n"
        )
        CONNECTION_RENEWED = (
            "Your connection to MicroStrategy Intelligence Server was renewed.\n"
        )
        CONNECTION_CLOSED = (
            "Connection to MicroStrategy Intelligence Server has been closed\n"
        )
        CONNECTION_STATUS_ACTIVE = (
            "Connection to MicroStrategy Intelligence Server is active.\n"
        )
        CONNECTION_STATUS_NOT_ACTIVE = (
            "Connection to MicroStrategy Intelligence Server is not active.\n"
        )
        CONNECTION_RENEWED_NOT_ACTIVE = """Connection with MicroStrategy Intelligence Server was not active.
                         \rNew connection has been established.\n"""

        username_std = self.username
        password_std = self.password
        base_url_std = self.url
        login_mode_std = self.login_mode
        project_id_std = self.project_id
        connection = con.get_connection(
            url=base_url_std,
            username=username_std,
            password=password_std,
            login_mode=login_mode_std,
            project_id=project_id_std,
        )

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.connect()
            self.assertEqual(mock_output.getvalue(), CONNECTION_CONNECT_RENEWED)

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.status()
            self.assertEqual(mock_output.getvalue(), CONNECTION_STATUS_ACTIVE)

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.renew()
            self.assertEqual(mock_output.getvalue(), CONNECTION_RENEWED)

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.close()
            self.assertEqual(mock_output.getvalue(), CONNECTION_CLOSED)

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.status()
            self.assertEqual(mock_output.getvalue(), CONNECTION_STATUS_NOT_ACTIVE)

        with patch("sys.stdout", new=StringIO()) as mock_output:
            connection.renew()
            self.assertEqual(mock_output.getvalue(), CONNECTION_RENEWED_NOT_ACTIVE)

    def check_connection_error(
        self, username, password, base_url, project_id, login_mode
    ):
        try:
            connection = con.get_connection(
                url=base_url,
                username=username,
                password=password,
                login_mode=login_mode,
                project_id=project_id,
            )
        except:
            return True
        return False

    def test_connection_no_prvlg(self):
        """TC65906"""
        # NOTE: when user lacks privileges to use connector,
        #       the error is thrown when he/she tries to log in
        username_no_prvlg = self.username_no_prvlg
        password_no_prvlg = self.password_no_prvlg
        base_url_no_prvlg = self.base_url_no_prvlg
        project_id_no_prvlg = self.project_id_no_prvlg
        login_mode_no_prvlg = self.login_mode_no_prvlg
        is_connection_error = self.check_connection_error(
            username_no_prvlg,
            password_no_prvlg,
            base_url_no_prvlg,
            project_id_no_prvlg,
            login_mode_no_prvlg,
        )
        self.assertEqual(is_connection_error, True)

    def test_connection_unsupported_ver(self):
        """TC65906"""
        # NOTE: when user tries to log in to environment with unsupported
        #       version of MSTR (below 11.1.4) the error is thrown
        username_no_supp = self.username_no_supp
        password_no_supp = self.password_no_supp
        base_url_no_supp = self.base_url_no_supp
        project_id_no_supp = self.project_id_no_supp
        login_mode_no_supp = self.login_mode_no_supp
        is_connection_error = self.check_connection_error(
            username_no_supp,
            password_no_supp,
            base_url_no_supp,
            project_id_no_supp,
            login_mode_no_supp,
        )
        self.assertEqual(is_connection_error, True)

    def test_connection_proxy(self):
        conn = con.get_connection(url=self.url,
                                  username=self.username,
                                  password=self.password,
                                  login_mode=self.login_mode,
                                  project_id=self.project_id,
                                  proxies=self.proxies)
        conn.connect()

    @staticmethod
    def get_ids(config, key, dataset):
        output = config[key][dataset]
        output = map(lambda x: x["id"], output)
        output = list(output)
        return output

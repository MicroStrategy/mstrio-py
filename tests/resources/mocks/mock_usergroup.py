import json
from copy import deepcopy
from unittest.mock import Mock


class MockUsergroup:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['usergroup']['all_usergroups']) as f:
        all_usergroups_data = json.load(f)

    with open(data_paths['usergroup']['create']) as f:
        create_usergroup_data = json.load(f)

    with open(data_paths['usergroup']['info']) as f:
        usergroup_info_data = json.load(f)

    with open(data_paths['usergroup']['add_members']) as f:
        add_members_data = json.load(f)

    with open(data_paths['usergroup']['add_memberships']) as f:
        add_memberships_data = json.load(f)

    with open(data_paths['usergroup']['privileges']) as f:
        privileges_data = json.load(f)

    with open(data_paths['usergroup']['settings']) as f:
        settings_data = json.load(f)

    @classmethod
    def mock_usergroups_api(cls):
        def mocked_create_user_group(connection, body):
            response = Mock(status_code=201)
            response.json.return_value = cls.create_usergroup_data
            return response

        def mocked_get_info_all_user_groups(connection, name_bagins, offset, limit, fields, error_msg):
            response = Mock(status_code=200)
            response.headers = {'x-mstr-total-count': 21}
            response.json.return_value = cls.all_usergroups_data
            return response

        def mocked_get_user_group_info(connection, id, error_msg):
            usrgroup_id_1 = 'D09773F94699124B4D75B48F1B358327'
            usrgroup_id_2 = '98AA5CA04DD6D20C6875C6B314874A1C'
            usrgroup_id_3 = 'E87FB53F46A623DA07C323A420DB1B49'

            tmp_return_value = deepcopy(cls.usergroup_info_data)
            if id == usrgroup_id_1 or id == usrgroup_id_2:
                tmp_return_value = deepcopy(cls.add_members_data)
                tmp_return_value['id'] = id
            elif id == usrgroup_id_3:
                tmp_return_value = deepcopy(cls.add_memberships_data)
                tmp_return_value['id'] = id

            response = Mock(status_code=200)
            response.json.return_value = tmp_return_value
            return response

        def mocked_update_user_group_info(connection, id, body):
            op = body['operationList'][0]['op']
            path = body['operationList'][0]['path']
            usrgroup_id_1 = 'D09773F94699124B4D75B48F1B358327'
            usrgroup_id_2 = '98AA5CA04DD6D20C6875C6B314874A1C'
            usrgroup_id_3 = 'E87FB53F46A623DA07C323A420DB1B49'
            usrgroup_id_4 = 'A51EE17B415A313F78DF4998743C4CCC'

            tmp_return_value = None
            if path == '/members':
                tmp_return_value = deepcopy(cls.add_members_data)
                if op == 'remove':
                    if id == usrgroup_id_1:
                        tmp_return_value['id'] = usrgroup_id_1
                        tmp_return_value['members'] = tmp_return_value['members'][:1]
                    elif id == usrgroup_id_2:
                        tmp_return_value['id'] = usrgroup_id_2
                        tmp_return_value['members'] = []
            elif path == '/memberships':
                tmp_return_value = deepcopy(cls.add_memberships_data)
                if op == 'remove':
                    tmp_return_value['id'] = usrgroup_id_3
                    tmp_return_value['memberships'] = tmp_return_value['memberships'][:1]
            elif path == '/privileges':
                tmp_return_value = deepcopy(cls.create_usergroup_data)
                if op == 'remove':
                    tmp_return_value['id'] = usrgroup_id_4

            response = Mock(status_code=201)
            response.json.return_value = tmp_return_value
            return response

        def mocked_get_privileges(connection, id, privilege_level, project_id, error_msg):
            usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'

            tmp_return_value = deepcopy(cls.privileges_data)
            if id != usrgroup_id:
                tmp_return_value['privileges'] = tmp_return_value['privileges'][:1]

            response = Mock(status_code=200)
            response.json.return_value = tmp_return_value
            return response

        def mocked_get_settings(connection, id, include_access):
            response = Mock(status_code=200)
            response.json.return_value = cls.settings_data
            return response

        mocked_usergroups = Mock()
        mocked_usergroups.get_info_all_user_groups = mocked_get_info_all_user_groups
        mocked_usergroups.create_user_group = mocked_create_user_group
        mocked_usergroups.get_user_group_info = mocked_get_user_group_info
        mocked_usergroups.update_user_group_info = mocked_update_user_group_info
        mocked_usergroups.get_privileges = mocked_get_privileges
        mocked_usergroups.get_settings = mocked_get_settings

        return mocked_usergroups

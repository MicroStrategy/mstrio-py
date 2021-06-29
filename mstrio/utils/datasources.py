import json


def alter_conn_resp(response):
    response_json = response.json()
    response_json = alter_conn_json(response_json)
    response.encoding, response._content = 'utf-8', json.dumps(response_json).encode('utf-8')
    return response


def alter_conn_list_resp(response):
    response_json = response.json()
    for conn in response_json["connections"]:
        alter_conn_json(conn)
    response.encoding, response._content = 'utf-8', json.dumps(response_json).encode('utf-8')
    return response


def alter_conn_json(response_json):
    response_json['datasource_login'] = response_json["database"]["login"]
    response_json['database_type'] = response_json["database"]["type"]
    response_json['database_version'] = response_json["database"]["version"]
    del response_json["database"]
    return response_json


def alter_instance_resp(response):
    response_json = response.json()
    response_json = alter_instance_json(response_json)
    response.encoding, response._content = 'utf-8', json.dumps(response_json).encode('utf-8')
    return response


def alter_instance_list_resp(response):
    response_json = response.json()
    for ds in response_json["datasources"]:
        alter_instance_json(ds)
    response.encoding, response._content = 'utf-8', json.dumps(response_json).encode('utf-8')
    return response


def alter_instance_json(response_json):
    response_json['datasource_connection'] = response_json["database"]["connection"]
    response_json['database_type'] = response_json["database"]["type"]
    response_json['database_version'] = response_json["database"]["version"]
    response_json['primary_datasource'] = response_json["database"].get("primaryDatasource")
    response_json['data_mart_datasource'] = response_json["database"].get("dataMartDatasource")
    del response_json["database"]
    return response_json


def alter_patch_req_body(op_dict, initial_path, altered_path):
    if op_dict["path"] == initial_path:
        op_dict["path"] = altered_path
        op_dict["value"] = op_dict["value"] if isinstance(op_dict["value"],
                                                          str) else op_dict["value"].get("id")
    return op_dict


def get_objects_id(obj, obj_class):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, obj_class):
        return obj.id
    return None

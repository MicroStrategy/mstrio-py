import json
from typing import Callable

from mstrio.api import test_center as tc_api

# pass-through so that modules do not import from api and processors
# at the same time
from mstrio.api.test_center import (  # noqa: F401
    bulk_delete_baseline_results,
    bulk_delete_baseline_tests,
    bulk_delete_comparison_results,
    bulk_delete_comparison_tests,
    cancel_baseline_run,
    cancel_comparison_run,
    create_comparison_test,
    delete_baseline_result,
    delete_baseline_test,
    delete_comparison_result,
    delete_comparison_test,
    get_all_baseline_results,
    get_all_comparison_results,
    get_all_comparison_tests,
    get_comparison_test,
    get_test_center_settings,
    run_baseline_test,
    run_comparison_test,
    sync_baseline_result,
    update_comparison_test,
    update_test_center_settings,
)
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.utils.helper import camel_to_snake, rename_dict_keys

# _REST_ATTR_MAP is defined further up, in EntityBase
SETTINGS_ATTR_MAP = {
    "sourcePrecedence": "promptAnswerSourcePrecedence",
    "dossierSqlEnabled": "dashboardSqlEnabled",
    "dossierDataEnabled": "dashboardDataEnabled",
    "dossierVisualizationScreenshotEnabled": "dashboardVisualizationScreenshotEnabled",
}


def _wrangle_settings_incoming(settings: dict) -> dict:
    """Wrangle settings for test creation and update."""
    settings = settings.copy()

    if "analyzer" in settings:
        settings.update(settings.pop("analyzer"))
    if "promptAnswer" in settings:
        settings.update(settings.pop("promptAnswer"))

    settings = rename_dict_keys(settings, SETTINGS_ATTR_MAP)
    settings = camel_to_snake(settings)

    return settings


def get_all_baseline_tests(connection: Connection, error_msg: str | None = None):
    res = tc_api.get_all_baseline_tests(connection=connection).json()
    baseline_tests = res.get("integrityTests", [])
    for blt in baseline_tests:
        blt["settings"] = _wrangle_settings_incoming(blt.get("settings", {}))
    return baseline_tests


def get_baseline_test(connection: Connection, id: str, error_msg: str | None = None):
    res = tc_api.get_baseline_test(connection=connection, id=id).json()
    res["settings"] = _wrangle_settings_incoming(res.get("settings", {}))
    return res


def _wrangle_summary(summary: dict) -> dict:
    """Wrangle summary for test result."""
    summary = summary.copy()

    summary.update(summary.pop("stats", {}))

    return {"summary": summary}


def get_baseline_result_summary(
    connection: Connection,
    test_id: str,
    id: str,
):
    res = tc_api.get_baseline_result_summary(
        connection=connection, test_id=test_id, id=id
    ).json()
    return _wrangle_summary(res)


def get_comparison_result_summary(
    connection: Connection,
    test_id: str,
    id: str,
):
    res = tc_api.get_comparison_result_summary(
        connection=connection, test_id=test_id, id=id
    ).json()
    return _wrangle_summary(res)


def _wrangle_settings_outgoing(settings: dict) -> dict:
    """Wrangle settings for test retrieval."""
    settings = settings.copy()
    attr_map = {v: k for k, v in SETTINGS_ATTR_MAP.items()}
    settings = rename_dict_keys(settings, attr_map)

    non_analyzer_settings = {
        "promptAnswer": {
            "sourcePrecedence": settings.pop("sourcePrecedence", None),
        },
        "executeContent": settings.pop("executeContent", None),
    }

    return {**non_analyzer_settings, "analyzer": settings}


def create_baseline_test(
    connection: Connection,
    body: dict,
):
    body["settings"] = _wrangle_settings_outgoing(body.get("settings", {}))
    res = tc_api.create_baseline_test(connection=connection, body=body).json()
    res["settings"] = _wrangle_settings_incoming(res.get("settings", {}))
    return res


def update_baseline_test(
    connection: Connection,
    id: str,
    body: dict,
):
    body["settings"] = _wrangle_settings_outgoing(body.get("settings", {}))
    res = tc_api.update_baseline_test(connection=connection, id=id, body=body).json()
    res["settings"] = _wrangle_settings_incoming(res.get("settings", {}))
    return res


def _parse_tree_structure(tree_structure: dict | None) -> list[tuple[str, str]]:
    if tree_structure is None:
        return [("", "")]  # no tree, single object result entry
    return [
        (viz.get("key", ""), viz.get("name", ""))
        for chapter in tree_structure.get("chapters", [])
        for page in chapter.get("pages", [])
        for viz in page.get("visualizations", [])
    ]


def _wrangle_baseline_object_results(
    object_result: dict, test_id: str, test_result_id: str
) -> list[dict]:
    """Wrangle object result for test result."""
    object_result = object_result.copy()

    tested_object = {
        "id": object_result.pop("objectId", None),
        "name": object_result.pop("objectName", None),
        "type": object_result.pop("objectType", None),
        "subtype": object_result.pop("objectSubType", None),
        "viewMedia": object_result.pop("viewMedia", None),
        "extType": object_result.pop("extType", None),
        "projectId": object_result.pop("projectId", None),
        "ancestors": object_result.pop("ancestors", []),
    }
    object_result["testedObject"] = tested_object

    tree_structure_str: str = object_result.pop("treeStructure", None)
    tree_structure = json.loads(tree_structure_str) if tree_structure_str else None
    object_result["treeStructure"] = tree_structure

    status = object_result.pop("status", [])
    sql_status = None
    data_status = None
    for s in status:
        if "sql_execution" in s.get("type", ""):
            sql_status = s.get("status")
        elif "data_execution" in s.get("type", ""):
            data_status = s.get("status")
    object_result["sqlStatus"] = sql_status
    object_result["dataStatus"] = data_status

    object_result["settings"] = _wrangle_settings_incoming(
        object_result.get("settings", {})
    )
    object_result["testId"] = test_id  # backlink
    object_result["resultId"] = test_result_id  # backlink

    viz_list = _parse_tree_structure(tree_structure)

    return [
        {
            **object_result,
            "vizKey": viz_key,
            "vizName": viz_name,
        }
        for viz_key, viz_name in viz_list
    ]


def _wrangle_comparison_object_results(
    object_result: dict, test_id: str, test_result_id: str
) -> list[dict]:
    """Wrangle object result for test result."""
    object_result = object_result.copy()

    per_key_summaries = object_result.pop("summary", {}).get("summary", {"": {}})

    object_result["testId"] = test_id  # backlink
    object_result["resultId"] = test_result_id  # backlink

    return [
        {
            **object_result,
            "vizKey": viz_key,
            "sqlStatus": per_key_summaries[viz_key].get("sql", "not_compared"),
            "dataStatus": per_key_summaries[viz_key].get("data", "not_compared"),
        }
        for viz_key in per_key_summaries
    ]


def get_baseline_result(
    connection: Connection,
    test_id: str,
    id: str,
):
    res = tc_api.get_baseline_result(
        connection=connection, test_id=test_id, id=id
    ).json()
    res_status = tc_api.get_baseline_result_status(
        connection=connection, test_id=test_id, id=id
    ).json()
    results_map = {o["baselineId"]: o for o in res.pop("testObjectBaselines", [])}
    status_map = {o["baselineId"]: o for o in res_status.pop("statuses", [])}
    for baseline_id in results_map:
        results_map[baseline_id].pop("status", None)
        if baseline_id in status_map:
            results_map[baseline_id] |= status_map[baseline_id]

    res["objectResults"] = [
        obj_result
        for source in results_map.values()
        for obj_result in _wrangle_baseline_object_results(
            source, test_id=test_id, test_result_id=id
        )
    ]

    return res


def get_object_result_detail(
    api_with_viz: Callable,
    api_without_viz: Callable,
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str | None = None,
):
    ids = {"test_id": test_id, "result_id": result_id, "id": id}
    try:
        res = (
            api_with_viz(connection=connection, **ids, viz_key=viz_key)
            if viz_key
            else api_without_viz(connection=connection, **ids)
        )
    except IServerError as e:
        if e.http_code == 404:
            return {}  # 404 expected if error running test
        else:
            raise
    return res.json()


def get_baseline_object_result_sql(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str | None = None,
):
    return get_object_result_detail(
        api_with_viz=tc_api.get_baseline_visualization_result_sql,
        api_without_viz=tc_api.get_baseline_object_result_sql,
        connection=connection,
        test_id=test_id,
        result_id=result_id,
        id=id,
        viz_key=viz_key,
    )


def get_baseline_object_result_data(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str | None = None,
):
    return get_object_result_detail(
        api_with_viz=tc_api.get_baseline_visualization_result_data,
        api_without_viz=tc_api.get_baseline_object_result_data,
        connection=connection,
        test_id=test_id,
        result_id=result_id,
        id=id,
        viz_key=viz_key,
    )


def get_comparison_result(
    connection: Connection,
    test_id: str,
    id: str,
):
    res = tc_api.get_comparison_result(
        connection=connection, test_id=test_id, id=id
    ).json()
    res_status = tc_api.get_comparison_result_status(
        connection=connection, test_id=test_id, id=id
    ).json()
    results_map = {o["comparisonId"]: o for o in res.pop("testObjectComparisons", [])}
    status_map = {o["comparisonId"]: o for o in res_status.pop("statuses", [])}
    for comparison_id in results_map:
        results_map[comparison_id].pop("status", None)
        if comparison_id in status_map:
            results_map[comparison_id] |= status_map[comparison_id]

    res["objectResults"] = [
        obj_result
        for source in results_map.values()
        for obj_result in _wrangle_comparison_object_results(
            source, test_id=test_id, test_result_id=id
        )
    ]

    return res


def get_comparison_object_result_sql_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str | None = None,
):
    res_json = get_object_result_detail(
        api_with_viz=tc_api.get_comparison_node_result_sql_diff,
        api_without_viz=tc_api.get_comparison_result_sql_diff,
        connection=connection,
        test_id=test_id,
        result_id=result_id,
        id=id,
        viz_key=viz_key,
    )
    return {"sqlDiff": res_json}


def get_comparison_object_result_data_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str | None = None,
):
    return get_object_result_detail(
        api_with_viz=tc_api.get_comparison_node_result_data_diff,
        api_without_viz=tc_api.get_comparison_result_data_diff,
        connection=connection,
        test_id=test_id,
        result_id=result_id,
        id=id,
        viz_key=viz_key,
    )

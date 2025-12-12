from typing import TYPE_CHECKING

from mstrio.api import custom_groups as cg_api

if TYPE_CHECKING:
    from mstrio.connection import Connection


def wrangle_incoming_body(response: dict) -> dict:
    for el in response.get("elements", []):
        if "displayOption" in el:
            el["display"] = el.pop("displayOption")
        if format := el.pop("format", None):
            el["elementFormat"] = {
                "values": format.get("values"),
                "header": format.get("header"),
            }
            el["itemsFormat"] = {
                "values": format.get("itemsValues"),
                "header": format.get("itemsHeaders"),
            }
    return response


def wrangle_outgoing_body(body: dict) -> dict:
    for el in body.get("elements", []):
        if "display" in el:
            el["displayOption"] = el.pop("display")
        format_body = {}
        if element_format := el.pop("elementFormat", None):
            format_body["values"] = element_format.get("values")
            format_body["header"] = element_format.get("header")
        if items_format := el.pop("itemsFormat", None):
            format_body["itemsValues"] = items_format.get("values")
            format_body["itemsHeaders"] = items_format.get("header")
        if format_body:
            el["format"] = format_body
    return body


def get_custom_group(
    connection: "Connection",
    id: str,
    project_id: str | None = None,
    changeset_id: str | None = None,
    show_expression_as: str | None = None,
    error_msg: str | None = None,
):
    response = cg_api.get_custom_group(
        connection=connection,
        id=id,
        project_id=project_id,
        changeset_id=changeset_id,
        show_expression_as=show_expression_as,
        error_msg=error_msg,
    ).json()
    return wrangle_incoming_body(response)


def create_custom_group(
    connection: "Connection",
    body: dict,
    project_id: str | None = None,
    show_expression_as: str | None = None,
    error_msg: str | None = None,
):
    response = cg_api.create_custom_group(
        connection=connection,
        body=wrangle_outgoing_body(body),
        project_id=project_id,
        show_expression_as=show_expression_as,
        error_msg=error_msg,
    ).json()
    return wrangle_incoming_body(response)

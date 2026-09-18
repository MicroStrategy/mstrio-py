from mstrio.api import subscription_assets as subscription_assets_api
from mstrio.connection import Connection


def list_images(connection: Connection, include_hidden: bool = False) -> list[dict]:
    """Return image dictionaries from the REST response."""
    response = subscription_assets_api.list_images(
        connection=connection,
        include_hidden=include_hidden,
    )
    return response.json().get('images', [])


def list_excel_templates(
    connection: Connection, include_hidden: bool = False
) -> list[dict]:
    """Return Excel template dictionaries from the REST response."""
    response = subscription_assets_api.list_excel_templates(
        connection=connection,
        include_hidden=include_hidden,
    )
    return response.json().get('excelTemplates', [])

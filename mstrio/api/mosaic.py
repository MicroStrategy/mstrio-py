from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error uploading Mosaic keytab file.")
def upload_mosaic_keytab(
    connection: Connection, file: bytes, file_name: str
) -> Response:
    """Upload a Mosaic keytab file to the local shared folder so other
    services can access it.

    The request is sent as `multipart/form-data` with two parts: `fileName`
    (original file name, used only for validation) and `file` (the keytab
    binary).

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        file (bytes): keytab file binary
        file_name (str): original file name of the keytab file (used only
            for validation)

    Return:
        HTTP response object. Expected status: 204
    """
    return connection.post(
        endpoint='/api/admin/mstrServices/mosaic/keytab',
        data={'fileName': file_name},
        files={'file': (file_name, file)},
    )


@ErrorHandler(err_msg="Error getting Mosaic settings.")
def get_mosaic_settings(connection: Connection, fields: str | None = None) -> Response:
    """Get Mosaic settings stored as files under universal semantic service.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        endpoint='/api/admin/mstrServices/mosaic/settings',
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error staging draft Mosaic settings.")
def stage_mosaic_settings(connection: Connection, body: dict) -> Response:
    """Save draft Mosaic settings to a sidecar file without modifying
    production config files. This allows saving work-in-progress
    configuration.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body with the Mosaic settings payload:
            {
                "krb5Realm": str,
                "domain": str (optional),
                "mosaicHost": str,
                "mosaicHostAliases": list[str] (optional),
                "mosaicSvc": str (optional),
                "keytabFileName": str,
                "upnDomains": list[str]
            }

    Return:
        HTTP response object. Expected status: 204
    """
    return connection.post(
        endpoint='/api/admin/mstrServices/mosaic/settings/stage',
        json=body,
    )


@ErrorHandler(err_msg="Error committing Mosaic settings.")
def commit_mosaic_settings(connection: Connection, body: dict) -> Response:
    """Commit Mosaic settings to production config files.

    The server will update config.properties, krb5.conf and user-mapping.json
    under universal semantic service. Requires existing baseline files. Also
    enables JWT authentication mode.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body with the Mosaic settings payload:
            {
                "krb5Realm": str,
                "domain": str (optional),
                "mosaicHost": str,
                "mosaicHostAliases": list[str] (optional),
                "mosaicSvc": str (optional),
                "keytabFileName": str,
                "upnDomains": list[str]
            }

    Return:
        HTTP response object. Expected status: 204
    """
    return connection.post(
        endpoint='/api/admin/mstrServices/mosaic/settings/commit',
        json=body,
    )

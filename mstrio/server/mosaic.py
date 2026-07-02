import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mstrio import config
from mstrio.api import mosaic as mosaic_api
from mstrio.connection import Connection
from mstrio.utils.helper import Dictable
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


class MosaicSettingsStatus(Enum):
    """Status of the Mosaic SSO configuration.

    `IN_PROGRESS` - settings are fetched from the sidecar (draft) file only.
    `COMMITTED` - settings are fetched from the main config files only.
    """

    IN_PROGRESS = 'IN_PROGRESS'
    COMMITTED = 'COMMITTED'


@dataclass
class MosaicSsoSettings(Dictable):
    """Mosaic SSO settings of an environment.

    Attributes:
        krb5_realm (str, optional): Kerberos realm (uppercase FQDN),
            e.g. CORP.MICROSTRATEGY.COM
        mosaic_host (str, optional): Mosaic host used in SPN/keytab principal
            (HTTP/<host>), e.g. demo.microstrategy.com
        keytab_file_name (str, optional): keytab file name (without any path).
            Written into config.properties as etc/<fileName>,
            e.g. mci-jpd9h-dev-http.keytab
        upn_domains (list[str], optional): all UPN domains. The first entry is
            used as email suffix in user-mapping.json.
        domain (str, optional): domain value used by UI and persisted for
            round-trip. Not directly patched into config files.
        mosaic_host_aliases (list[str], optional): Mosaic host aliases used by
            UI and persisted for round-trip. Not patched into
            config.properties.
        mosaic_svc (str, optional): Mosaic service account value used by UI
            and persisted for round-trip. Not directly patched into config
            files.
        status (MosaicSettingsStatus, optional): status of the configuration.
            Read-only, server-populated. Stripped from request bodies when
            staging or committing settings.
    """

    _FROM_DICT_MAP = {
        'status': MosaicSettingsStatus,
    }

    krb5_realm: str | None = None
    mosaic_host: str | None = None
    keytab_file_name: str | None = None
    upn_domains: list[str] | None = None
    domain: str | None = None
    mosaic_host_aliases: list[str] | None = None
    mosaic_svc: str | None = None
    status: MosaicSettingsStatus | str | None = None


def _prepare_settings_body(settings: MosaicSsoSettings | dict) -> dict:
    """Convert settings to a camelCase request body, stripping the read-only
    `status` field."""
    body = settings.to_dict() if isinstance(settings, Dictable) else dict(settings)
    body.pop('status', None)
    return body


@method_version_handler('11.6.0100')
def get_mosaic_settings(connection: Connection) -> MosaicSsoSettings:
    """Get Mosaic SSO settings stored as files under universal semantic
    service.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`

    Returns:
        MosaicSsoSettings object with the current Mosaic settings.
    """
    response = mosaic_api.get_mosaic_settings(connection)
    return MosaicSsoSettings.from_dict(response.json())


@method_version_handler('11.6.0100')
def stage_mosaic_settings(
    connection: Connection, settings: MosaicSsoSettings | dict
) -> None:
    """Save draft Mosaic SSO settings to a sidecar file without modifying
    production config files. This allows saving work-in-progress
    configuration.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        settings (MosaicSsoSettings, dict): Mosaic settings to stage. The
            read-only `status` field is stripped before sending.

    Returns:
        None
    """
    mosaic_api.stage_mosaic_settings(connection, body=_prepare_settings_body(settings))
    if config.verbose:
        logger.info('Draft Mosaic settings have been staged.')


@method_version_handler('11.6.0100')
def commit_mosaic_settings(
    connection: Connection, settings: MosaicSsoSettings | dict
) -> None:
    """Commit Mosaic SSO settings to production config files.

    The server will update config.properties, krb5.conf and user-mapping.json
    under universal semantic service. Requires existing baseline files. Also
    enables JWT authentication mode.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        settings (MosaicSsoSettings, dict): Mosaic settings to commit. The
            read-only `status` field is stripped before sending.

    Returns:
        None
    """
    mosaic_api.commit_mosaic_settings(connection, body=_prepare_settings_body(settings))
    if config.verbose:
        logger.info('Mosaic settings have been committed.')


@method_version_handler('11.6.0100')
def upload_mosaic_keytab(
    connection: Connection,
    file: str | Path | bytes,
    file_name: str | None = None,
) -> None:
    """Upload a Mosaic keytab file to the local shared folder so other
    services can access it.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        file (str, Path, bytes): path to the keytab file or its binary
            content
        file_name (str, optional): original file name of the keytab file
            (used by the server for validation). Defaults to the base name
            of `file` when a path is provided. Required when `file` is
            passed as bytes.

    Returns:
        None
    """
    if isinstance(file, (str, Path)):
        path = Path(file)
        file_name = file_name or path.name
        file = path.read_bytes()
    elif file_name is None:
        raise ValueError("'file_name' must be provided when 'file' is passed as bytes.")
    mosaic_api.upload_mosaic_keytab(connection, file=file, file_name=file_name)
    if config.verbose:
        logger.info(f"Mosaic keytab file '{file_name}' has been uploaded.")

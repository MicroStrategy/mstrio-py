# Test all datasource connections.

from mstrio import config
from mstrio.connection import get_connection, Connection
from mstrio.datasources import list_datasource_instances, DatasourceConnection

config.verbose = False

# Suppress default logging if verbose output is disabled
if not config.verbose:
    for hdlr in config.logger.handlers:
        hdlr.setLevel(50)


logger = config.logger


def test_all_datasources(conn: Connection, show_embedded: bool = False) -> None:
    datasources = list_datasource_instances(connection=conn)

    for ds in datasources:
        if isinstance(ds.datasource_connection, DatasourceConnection):
            try:
                test_results = ds.datasource_connection.test_connection()
                logger.info(
                    f"{'Success' if test_results else 'Failure'}  {ds.name}; DBC: "
                    f"'{ds.datasource_connection.name}'; DBL: "
                    f"'{ds.datasource_connection.datasource_login.name}' "
                    f"({ds.datasource_connection.datasource_login.username})"
                )
            except Exception as e:
                logger.error(
                    f"[Error]: {ds.name}; DBC: '{ds.datasource_connection.name}': "
                    f"{str(e) if config.verbose else str(e).splitlines()[0]}"
                )
        else:
            if show_embedded:
                logger.info(
                    f"[Warning]: No test {ds.name}; Embedded connection, test "
                    "not available"
                )


conn = get_connection(connectionData)

test_all_datasources(conn=conn, show_embedded=True)

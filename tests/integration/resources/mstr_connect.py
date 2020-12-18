try:
    from mstrio.connection import Connection
except ModuleNotFoundError:
    from mstrio.microstrategy import Connection


def get_connection(url, username, password, project_id, login_mode,
                   verbose=True, proxies=None):
    connection = Connection(base_url=url,
                            username=username,
                            password=password,
                            project_id=project_id,
                            login_mode=login_mode,
                            proxies=proxies)
    return connection

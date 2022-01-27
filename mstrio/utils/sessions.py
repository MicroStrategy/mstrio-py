import functools
from requests_futures.sessions import FuturesSession


class FuturesSessionWithRenewal(FuturesSession):

    def __init__(self, *, connection, **kwargs):
        super().__init__(session=connection._session, **kwargs)
        self.connection = connection

    def request(self, *args, **kwargs):
        if self.connection._is_session_expired():
            self.connection._renew_or_reconnect()

        return super().request(*args, **kwargs)


def renew_session(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not kwargs.pop('skip_expiration_check', False) and self._is_session_expired():
            self._renew_or_reconnect()

        return func(self, *args, **kwargs)

    return wrapper

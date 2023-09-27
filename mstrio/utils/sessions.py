import functools
import logging

from requests_futures.sessions import FuturesSession


class FuturesSessionWithRenewal(FuturesSession):
    def __init__(self, *, connection, **kwargs):
        super().__init__(session=connection._session, **kwargs)
        self.connection = connection

    def request(self, *args, **kwargs):
        if self.connection._is_session_expired():
            self.connection._renew_or_reconnect()

        return super().request(*args, **kwargs)

    def get(self, *, endpoint, **kwargs):
        r"""
        Sends a GET request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).get(url, **kwargs)

    def options(self, *, endpoint, **kwargs):
        r"""Sends a OPTIONS request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).options(url, **kwargs)

    def head(self, *, endpoint, **kwargs):
        r"""Sends a HEAD request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).head(url, **kwargs)

    def post(self, *, endpoint, data=None, json=None, **kwargs):
        r"""Sends a POST request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of
            the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).post(url, data=data, json=json, **kwargs)

    def put(self, *, endpoint, data=None, **kwargs):
        r"""Sends a PUT request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).put(url, data=data, **kwargs)

    def patch(self, *, endpoint, data=None, **kwargs):
        r"""Sends a PATCH request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).patch(url, data=data, **kwargs)

    def delete(self, *, endpoint, **kwargs):
        r"""Sends a DELETE request. Returns :class:`Future` object.

        :param endpoint: endpoint that will be combined with
            `self.connection.base_url`for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype : concurrent.futures.Future
        """
        url = self.connection.base_url + endpoint

        return super(FuturesSession, self).delete(url, **kwargs)


def renew_session(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if (
            not kwargs.pop('skip_expiration_check', False)
            and self._is_session_expired()
        ):
            self._renew_or_reconnect()

        return func(self, *args, **kwargs)

    return wrapper


def log_request(logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, method_name, url=None, endpoint=None, **kwargs):
            if logger.isEnabledFor(logging.DEBUG):
                log_url = url or self.base_url + endpoint
                logger.debug("method = %s url = '%s'", method_name, log_url)
                logger.debug("headers = %s", self._session.headers)
                logger.debug("headers additional = %s", kwargs.get('headers'))
                logger.debug("body = %s", kwargs.get('json'))
            return func(self, method_name, url=url, endpoint=endpoint, **kwargs)

        return wrapper

    return decorator

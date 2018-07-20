import logging

logger = logging.getLogger('mstr')


def log_http_response(r, lvl = logging.WARNING):
    logger.log(lvl, f'HTTP {r.status_code} - {r.reason}, Message {r.text}')

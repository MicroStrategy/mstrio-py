import re
import warnings
import os

__DEBUG = False

def debug():
    return __DEBUG

def set_debug(debug):
    global __DEBUG
    __DEBUG = debug

def url_check(url):
    """Checks the validity of the url for microstrategy object initialization and returns a validated url."""
    regex = r'^https?://.+$'
    match = re.search(regex, url)
    api_index = url.find('/api')

    if match is None:
        raise ValueError(
            "Please check the validity of the base_url parameter. Typically of the form 'https://<<MSTR Domain>>/MicroStrategyLibrary/'")
    if api_index != -1:
        url = url[:api_index]
    if url.endswith('/'):
        url = url[:-1]

    return url


def exception_handler(msg, exception_type=Exception, throw_error=True, stack_lvl=2):
    """Generic error message handler.

    Args:
        msg (str): Message to print in addition to any server-generated error message(s).
        throw_error (bool): Flag indicates if the error should be thrown
    """

    if throw_error:
        raise exception_type(msg)
    else:
        warnings.warn(msg, exception_type, stacklevel=stack_lvl)


def response_handler(response, msg, throw_error=True, verbose=True):
    """Generic error message handler for transactions against datasets.

    Args:
        response: Response object returned by HTTP request.
        msg (str): Message to print in addition to any server-generated error message(s).
        throw_error (bool): Flag indicates if the error should be thrown
    """

    if response.status_code == 204:
        error_msg = "204 No Content: I-Server successfully processed the request but did not return any content."
        exception_handler(msg=error_msg, exception_type=Warning, throw_error=False)
    else:
        if verbose: print("\n" + msg)
        try:
            res = response.json()
            if verbose: print("\nI-Server Error %s, %s" % (res['code'], res['message']))
        except Exception:
            if verbose: print("\nCould not decode the response from the I-Server. Please check if I-Server is running correctly.")
        finally:
            if throw_error:
                response.raise_for_status()


def get_parallel_number(total_chunks):
    """Returns the optimal number of threads to be used for downloading cubes/reports in parallel"""

    threads = min(8, os.cpu_count() + 4)
    if (total_chunks > 0):
        threads = min(total_chunks, threads)

    return threads

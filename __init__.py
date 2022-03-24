import logging

logger = logging.getLogger(__name__)


def _get_mstrio_py_versioning():
    """Method displaying current mstrio-py versioning, with details.

    To be compared with values found here:
    [mstrio-py github]/production/mstrio/__init__.py

    Example:
        from __init__ import _get_mstrio_py_versioning
        print(_get_mstrio_py_versioning())

    Returns:
        Object with example structure as follows:
        {
            'release_version': '11.3.3.101',
            'development_version': 1000,
            'full_version': '11.3.3.101_1000'
        }
    """
    try:
        from mstrio import __version__, __dev_version__
    except ImportError:
        logger.error('Error importing versions values: check mstrio-py package instalation.')

    __version__ = __version__ if "__version__" in locals() else None
    __dev_version__ = __dev_version__ if "__dev_version__" in locals() else None
    return {
        "release_version": __version__,
        "development_version": __dev_version__,
        "full_version": (
            str(__version__) + '_' + str(__dev_version__)
            if __version__ and __dev_version__ else None),
    }

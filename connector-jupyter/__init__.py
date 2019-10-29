# from .version import version_info, __version__


def _jupyter_nbextension_paths():
    return [dict(section="notebook",
                 src="production/mstr_jupyter/static",
                 dest="mstr_jupyter",
                 require="mstr_jupyter/main")]

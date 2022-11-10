def _jupyter_nbextension_paths():
    return [dict(section="notebook",
                 src="production/mstr_jupyter/static",
                 dest="mstr_jupyter",
                 require="mstr_jupyter/main")]

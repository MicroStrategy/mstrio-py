from json.decoder import JSONDecodeError
import logging
import os

from mstrio.utils.helper import exception_handler

logger = logging.getLogger(__name__)


def print_url(response, *args, **kwargs):
    """Response hook to print url for debugging."""
    logger.debug(response.url)


def save_response(response, *args, **kwargs):
    """Response hook to save REST API responses to files structured by the API
    family."""
    import json
    from pathlib import Path

    if response.status_code != 204:

        # Generate file name
        base_path = Path(__file__).parents[2] / 'tests/resources/auto-api-responses/'
        url = response.url.rsplit('api/', 1)[1]
        temp_path = url.split('/')
        file_name = '-'.join(temp_path[1:]) if len(temp_path) > 1 else temp_path[0]
        file_name = f'{file_name}-{response.request.method}'
        file_path = base_path if len(temp_path) == 1 else base_path / temp_path[0]
        path = str(file_path / file_name)

        # Create target directory & all intermediate directories if don't exists
        if not os.path.exists(str(file_path)):
            os.makedirs(file_path)
            print("Directory ", file_path, " created ")
        else:
            print("Directory ", file_path, " already exists")

        # Dump the response to JSON and Pickle
        # with open(path + '.pkl', 'wb') as f:
        #     pickle.dump(response, f)
        with open(path + '.json', 'w') as f:
            try:
                json.dump(response.json(), f)
            except JSONDecodeError:
                exception_handler("Could not decode response. Skipping creating JSON file.",
                                  Warning)

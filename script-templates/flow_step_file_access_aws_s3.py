"""
Flow Step Template: Manipulate AWS S3 files
Script Result Type: ---

This workflow template works OOTB after providing values for all required
Variables.

It represents File Manipulation on AWS S3 action.

This template supports the following actions, all configured via dedicated Variables:

- $source_action == `create`:
    requires following Variables: `$target_file`
    optional Variables: `$new_content`, `$list_of_find_text`, `$list_of_replace_with`

- $source_action == `delete`:
    requires following Variables: `$source_file` OR `$source_folder`
    optional Variables: None

- $source_action == `copy`: OR
- $source_action == `move`: OR
- $source_action == `rename`:
    requires following Variables:
        `$source_file` + `$target_file` OR
        `$source_folder` + `$target_folder`
    optional Variables: `$list_of_find_text`, `$list_of_replace_with`

Optional Variables Use Clarifications:

- `$new_content`: When creating a file, this represents its content
- `$list_of_find_text`: list of strings representing what is supposed to be replaced in files content
- `$list_of_replace_with`: list of strings representing replacements for hits from `$list_of_find_text`

Values from `$list_of_find_text` and `$list_of_replace_with` will be matched
one by one, meaning:

- `$list_of_find_text`     ["a", "b", ...]
- `$list_of_replace_with`  ["x", "z", ...]

Will replace all "a"'s with "x"'s (first items) and all "b"'s with "z"'s (second items), etc.

EXAMPLES:

>>> $source_action == `delete`
>>> $source_file == `some/path/file.txt`
>>> ---
>>> # this will delete file `some/path/file.txt` from S3 bucket

>>> $source_action == `copy`
>>> $source_folder == `some/path/`
>>> $target_folder == `other/subpath/`
>>> $list_of_find_text = ["ProjectID", "ObjectID"]
>>> $list_of_replace_with = ["1234QWER", "ZXCV0987"]
>>> ---
>>> # this will copy all files with `some/path/` prefix to a new target prefix
>>> # `other/subpath/` and the content in target files will be modified replacing
>>> # all instances of `ProjectID` with `1234QWER` and all instances of `ObjectID` with `ZXCV0987`

The workflow currently assumes:
- AWS S3 Bucket has been created and configured
- Runtime on which the script created from this template will be run has access
    to proper AWS domain with provided bucket data
"""

import datetime
from enum import Enum
import hashlib
import hmac
import urllib.parse
import requests
import xml


ACCESS_KEY_ID = $aws_access_key_id
SECRET_ACCESS_KEY = $aws_secret_access_key
REGION = $aws_region
BUCKET_NAME = $aws_bucket_name


def parsed(txt: str, non_param: bool = False) -> str:
    return urllib.parse.quote(txt, safe="/~" if non_param else "~-._")


def send_request(
    method: str, path: str, payload: str = "", params: dict[str, str] = None
):
    if not params:
        params = {}
    service = "s3"
    payload = payload.encode("utf-8")
    host = f"{BUCKET_NAME}.s3.{REGION}.amazonaws.com"
    endpoint_path = "/" + parsed(path, True)
    query_str = ""
    if params:
        pairs = sorted([(parsed(k), parsed(v)) for k, v in params.items()])
        query_str = "&".join([f"{k}={v}" for k, v in pairs])

    # SigV4 uses UTC
    t = datetime.datetime.now(tz=datetime.timezone.utc)
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    content_sha256 = hashlib.sha256(payload).hexdigest()

    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-content-sha256:{content_sha256}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "host;x-amz-content-sha256;x-amz-date"

    canonical_request = "\n".join(
        [
            method,
            endpoint_path,
            query_str,
            canonical_headers,
            signed_headers,
            content_sha256,
        ]
    )

    canonical_request_hash = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{REGION}/s3/aws4_request"
    string_to_sign = "\n".join(
        [algorithm, amz_date, credential_scope, canonical_request_hash]
    )

    def _sign(key, msg):
        if isinstance(key, str):
            key = key.encode("utf-8")
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        return hmac.new(key, msg, hashlib.sha256).digest()

    k_date = _sign("AWS4" + SECRET_ACCESS_KEY, date_stamp)
    k_region = _sign(k_date, REGION)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")

    signature = hmac.new(
        k_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization_header = (
        f"{algorithm} "
        f"Credential={ACCESS_KEY_ID}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    url = f"https://{host}{endpoint_path}"
    if query_str:
        url += "?" + query_str

    headers = {
        "Authorization": authorization_header,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": content_sha256,
        "Content-Type": "text/plain; charset=utf-8",
        # Optional but common:
        "Content-Length": str(len(payload)),
    }

    ret = requests.request(method, url, headers=headers, data=payload)

    return (
        ret.status_code,
        ret.text,
        (
            None
            if not ret.text.startswith("<?xml")
            else xml.etree.ElementTree.fromstring(ret.text)
        ),
    )


def get_file_content(path: str) -> str | None:
    code, content, _ = send_request("GET", path)
    if code >= 300:
        raise RuntimeError(f"File '{path}' does not exist or could not be found.")
    return content


def save_content_to_file(path: str, content: str) -> None:
    code, _, _ = send_request("PUT", path, content)
    if code >= 300:
        raise RuntimeError(f"Could not store content into '{path}' file.")


def create_empty_file(path: str) -> None:
    save_content_to_file(path, "")


def delete_file(path: str) -> None:
    code, _, _ = send_request("DELETE", path)
    if code >= 300:
        raise RuntimeError(f"Could not delete file '{path}'.")


def copy_file(source_path: str, target_path: str) -> None:
    source_content = get_file_content(source_path)
    save_content_to_file(target_path, source_content)


def move_file(source_path: str, target_path: str) -> None:
    copy_file(source_path, target_path)
    delete_file(source_path)


def list_files_with_prefix(prefix: str) -> list[str]:
    code, _, xml_tree = send_request(
        "GET", "", params={"list-type": "2", "prefix": prefix, "max-keys": "1000"}
    )
    if code >= 300:
        raise RuntimeError(f"Could not get files with prefix '{prefix}'.")
    return [
        next(v.text for v in el.iter() if v.tag.endswith("Key"))
        for el in xml_tree.iter()
        if el.tag.endswith("Contents")
    ]


class Action(Enum):
    COPY = 'copy'
    CREATE = 'create'
    DELETE = 'delete'
    MOVE = 'move'
    RENAME = 'rename'


try:
    ACTION = $source_action
    ACTION = Action(ACTION.lower())
except ValueError:
    raise RuntimeError(
        f"Invalid action '{ACTION}' provided. Valid actions are: {[a.value for a in Action]}."
    )

SOURCE_FILE = $source_file
SOURCE_FOLDER = $source_folder
TARGET_FILE = $target_file
TARGET_FOLDER = $target_folder
LIST_OF_FIND_TEXT = $list_of_find_text
LIST_OF_REPLACE_WITH = $list_of_replace_with
NEW_CONTENT = $new_content

content_to_be_manipulated = LIST_OF_FIND_TEXT and LIST_OF_REPLACE_WITH


def apply_find_and_replace(txt: str) -> str:
    for f, r in zip(LIST_OF_FIND_TEXT, LIST_OF_REPLACE_WITH, strict=True):
        txt = txt.replace(f, r)

    return txt


# Validation
match ACTION:
    case Action.COPY | Action.MOVE | Action.RENAME:
        assert bool(SOURCE_FILE and TARGET_FILE) ^ bool(SOURCE_FOLDER and TARGET_FOLDER), (
            f"Either both SOURCE_FILE and TARGET_FILE or both SOURCE_FOLDER and TARGET_FOLDER must be provided for {ACTION.value} action (but not neither nor all)."
        )
        assert not NEW_CONTENT, (
            f"NEW_CONTENT should not be provided for {ACTION.value} action."
        )

    case Action.CREATE:
        assert TARGET_FILE, "TARGET_FILE must be provided for create action."
        assert not any([SOURCE_FILE, SOURCE_FOLDER, TARGET_FOLDER]), (
            "SOURCE_FILE, SOURCE_FOLDER and TARGET_FOLDER should not be provided for create action."
        )

    case Action.DELETE:
        assert bool(SOURCE_FILE) ^ bool(SOURCE_FOLDER), (
            "Either SOURCE_FILE or SOURCE_FOLDER must be provided for delete action (but not neither nor both)."
        )
        assert not any([TARGET_FILE, TARGET_FOLDER]), (
            "TARGET_FILE and TARGET_FOLDER should not be provided for delete action."
        )
        assert not content_to_be_manipulated, (
            "LIST_OF_FIND_TEXT and LIST_OF_REPLACE_WITH should not be provided for delete action."
        )
        assert not NEW_CONTENT, (
            "NEW_CONTENT should not be provided for delete action."
        )


    case _:
        raise RuntimeError(f"Unknown action: '{ACTION}'")


def zip_sources_and_targets():
    if SOURCE_FILE:  # single file
        return zip(
            [SOURCE_FILE],
            [TARGET_FILE]
        )
    else:  # all from "folder" (aka: all with prefix)
        sources = list_files_with_prefix(SOURCE_FOLDER)
        return zip(
            sources,
            [s.replace(SOURCE_FOLDER, TARGET_FOLDER, 1) for s in sources]
        )


# Gather Content (plus apply manipulation if needed)
match ACTION:
    case Action.COPY | Action.MOVE | Action.RENAME:
        for s, t in zip_sources_and_targets():
            if content_to_be_manipulated:
                cont = apply_find_and_replace(get_file_content(s))
                save_content_to_file(t, cont)
            else:
                copy_file(s, t)

            if ACTION in [Action.MOVE, Action.RENAME]:
                delete_file(s)

    case Action.CREATE:
        try:
            get_file_content(TARGET_FILE)
        except RuntimeError:  # does not exist - expected
            cont = apply_find_and_replace(NEW_CONTENT) if content_to_be_manipulated else NEW_CONTENT
            save_content_to_file(TARGET_FILE, cont)
        else:  # raised, so exists - unexpected
            raise RuntimeError(f"File '{TARGET_FILE}' already exists.")

    case Action.DELETE:
        files = [SOURCE_FILE] if SOURCE_FILE else list_files_with_prefix(SOURCE_FOLDER)
        for f in files:
            delete_file(f)

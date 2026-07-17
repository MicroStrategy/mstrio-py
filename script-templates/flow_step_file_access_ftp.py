"""
Flow Step Template: Manipulate files via FTP
Script Result Type: ---

This workflow template works OOTB after providing values for all required
Variables.

It represents File Manipulation via FTP action.

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
>>> # this will delete file `some/path/file.txt` from FTP server

>>> $source_action == `copy`
>>> $source_folder == `some/path/`
>>> $target_folder == `other/subpath/`
>>> $list_of_find_text = ["ProjectID", "ObjectID"]
>>> $list_of_replace_with = ["1234QWER", "ZXCV0987"]
>>> ---
>>> # this will copy all files in `some/path/` folder to a new target folder
>>> # `other/subpath/` and the content in target files will be modified replacing
>>> # all instances of `ProjectID` with `1234QWER` and all instances of `ObjectID` with `ZXCV0987`

The workflow currently assumes:
- FTP Server has been set up and configured, and is on a public IP
- Runtime on which the script created from this template will be run has access
    to proper FPS domain
- Unless explicitly set otherwise, default encoding in data transfer is "utf-8"
"""

import contextlib
from enum import Enum
from ftplib import FTP
import io


HOST = $host_address
USERNAME = $username
PASSWORD = $password
ENCODING = $encoding or "utf-8"


def _split_path(path: str) -> tuple[str, str]:
    path = path.replace("\\", "/")
    if path.endswith("/") and path != "/":
        path = path[:-1]
    parent = "/".join(path.split("/")[:-1]) or "."
    name = path.split("/")[-1] if "/" in path else path
    return parent, name


def _clean_path(parent: str, file_name: str) -> str:
    return f"{parent}/{file_name}".replace(r"//", r"/")


def _cwd(ftp: FTP, dirpath: str) -> None:
    if dirpath in (".", ""):
        return
    ftp.cwd(dirpath)


@contextlib.contextmanager
def _get_ftp():
    with FTP() as ftp:
        ftp.connect(HOST, 21)
        ftp.login(USERNAME, PASSWORD)
        yield ftp


def read_file(path: str) -> str:
    data = bytearray()
    with _get_ftp() as ftp:
        ftp.retrbinary(f"RETR {path}", data.extend)

    return bytes(data).decode(ENCODING)


def write_to_file(path: str, content: str) -> None:
    data = content.encode(ENCODING)
    with _get_ftp() as ftp:
        ftp.storbinary(f"STOR {path}", io.BytesIO(data))


def file_exists(path: str) -> bool:
    with _get_ftp() as ftp:
        try:
            ftp.size(path)
            return True
        except Exception:
            return False


def folder_exists(path: str) -> bool:
    with _get_ftp() as ftp:
        cwd = ftp.pwd()
        try:
            _cwd(ftp, path)
            return True
        except Exception:
            return False
        finally:
            ftp.cwd(cwd)


def create_folder(path: str) -> None:
    parent, name = _split_path(path)

    with _get_ftp() as ftp:
        _cwd(ftp, parent)

        if not folder_exists(name):
            ftp.mkd(name)


def list_files_in_folder(path: str) -> list[str]:
    with _get_ftp() as ftp:
        _cwd(ftp, path)
        return [_clean_path(path, file_name) for file_name in ftp.nlst()]


def copy_file(source_path: str, target_path: str) -> None:
    content = read_file(source_path)
    write_to_file(target_path, content)


def move_file_or_folder(source_path: str, target_path: str) -> None:
    with _get_ftp() as ftp:
        ftp.rename(source_path, target_path)


def delete_file(path: str) -> None:
    with _get_ftp() as ftp:
        ftp.delete(path)


def delete_folder(path: str) -> None:
    items = list_files_in_folder(path)

    for item in items:
        try:
            # try as file
            delete_file(item)
        except Exception:
            # most likely failed because item is a folder
            delete_folder(item)

    with _get_ftp() as ftp:
        ftp.rmd(path)


def copy_folder(source_path: str, target_path: str) -> None:
    # ensure destination root exists
    create_folder(target_path)

    items = list_files_in_folder(source_path)

    for item in items:
        _, name = _split_path(item)
        target_item = _clean_path(target_path, name)

        try:
            # try as file
            copy_file(item, target_item)
        except Exception:
            # most likely failed because item is a folder
            copy_folder(item, target_item)


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
        assert bool(TARGET_FILE) ^ bool(TARGET_FOLDER), (
            "Either TARGET_FILE or TARGET_FOLDER must be provided for create action (but not neither nor both)."
        )
        assert not any([SOURCE_FILE, SOURCE_FOLDER]), (
            "SOURCE_FILE and SOURCE_FOLDER should not be provided for create action."
        )
        if TARGET_FOLDER:
            assert not NEW_CONTENT, (
                "NEW_CONTENT should not be provided for create action when TARGET_FOLDER is provided."
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


# Gather Content (plus apply manipulation if needed)
match ACTION:
    case Action.COPY:
        if SOURCE_FILE:  # single file work
            copy_file(SOURCE_FILE, TARGET_FILE)

        else:  # folder work
            copy_folder(SOURCE_FOLDER, TARGET_FOLDER)

    case Action.MOVE | Action.RENAME:
        move_file_or_folder(SOURCE_FILE or SOURCE_FOLDER, TARGET_FILE or TARGET_FOLDER)

    case Action.CREATE:
        if TARGET_FILE:  # single file work
            if file_exists(TARGET_FILE):
                raise RuntimeError(f"File '{TARGET_FILE}' already exists.")
            write_to_file(TARGET_FILE, NEW_CONTENT)

        else:  # folder work
            if folder_exists(TARGET_FOLDER):
                raise RuntimeError(f"Folder '{TARGET_FOLDER}' already exists.")
            create_folder(TARGET_FOLDER)

    case Action.DELETE:
        if SOURCE_FILE:  # single file work
            if file_exists(SOURCE_FILE):
                delete_file(SOURCE_FILE)

        else:  # folder work
            if folder_exists(SOURCE_FOLDER):
                delete_folder(SOURCE_FOLDER)

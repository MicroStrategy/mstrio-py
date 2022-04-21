from enum import Enum
import sys
from typing import List, TYPE_CHECKING, Union

from mstrio.access_and_security.security_filter import SecurityFilter  # noqa: F401
from mstrio.access_and_security.security_role import SecurityRole  # noqa: F401
from mstrio.datasources import DatasourceConnection  # noqa: F401
from mstrio.datasources import DatasourceInstance, DatasourceLogin  # noqa: F401
from mstrio.distribution_services.schedule import Schedule  # noqa: F401
from mstrio.object_management.folder import Folder  # noqa: F401
from mstrio.object_management.object import Object
from mstrio.object_management.search_operations import SearchObject  # noqa: F401
from mstrio.project_objects import Document, Report  # noqa: F401
from mstrio.project_objects.datasets import OlapCube, SuperCube  # noqa: F401
from mstrio.server import Project  # noqa: F401
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User, UserGroup  # noqa: F401
from mstrio.modeling.schema import Attribute  # noqa: F401

if TYPE_CHECKING:
    from mstrio.connection import Connection


class TypeObjectMapping(Enum):
    Report = ObjectTypes.REPORT_DEFINITION  # noqa: F811
    Folder = ObjectTypes.FOLDER  # noqa: F811
    DatasourceInstance = ObjectTypes.DBROLE  # noqa: F811
    DatasourceLogin = ObjectTypes.DBLOGIN  # noqa: F811
    DatasourceConnection = ObjectTypes.DBCONNECTION  # noqa: F811
    Project = ObjectTypes.PROJECT  # noqa: F811
    SecurityRole = ObjectTypes.SECURITY_ROLE  # noqa: F811
    Schedule = ObjectTypes.SCHEDULE_TRIGGER  # noqa: F811
    Document = ObjectTypes.DOCUMENT_DEFINITION  # noqa: F811
    SecurityFilter = ObjectTypes.SECURITY_FILTER  # noqa: F811
    SearchObject = ObjectTypes.SEARCH  # noqa: F811
    Attribute = ObjectTypes.ATTRIBUTE  # noqa: F811


class SubTypeObjectMapping(Enum):
    OlapCube = ObjectSubTypes.OLAP_CUBE  # noqa: F811
    SuperCube = ObjectSubTypes.SUPER_CUBE  # noqa: F811
    User = ObjectSubTypes.USER  # noqa: F811
    UserGroup = ObjectSubTypes.USER_GROUP  # noqa: F811


def __str_to_class(classname):
    return getattr(sys.modules[__name__], classname)


def map_to_object(object_type: Union[int, ObjectTypes], subtype: Union[int,
                                                                       ObjectSubTypes] = None):
    if not isinstance(object_type, ObjectTypes):
        try:
            object_type = ObjectTypes(object_type)
        except ValueError:
            object_type = None
    if not isinstance(subtype, ObjectSubTypes):
        try:
            subtype = ObjectSubTypes(subtype)
        except ValueError:
            subtype = None

    if ((object_type == ObjectTypes.REPORT_DEFINITION
         and subtype in (ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE))
            or (object_type == ObjectTypes.USER
                and subtype in (ObjectSubTypes.USER, ObjectSubTypes.USER_GROUP))):
        return __str_to_class(SubTypeObjectMapping(subtype).name)
    elif object_type in [v.value for v in TypeObjectMapping]:
        return __str_to_class(TypeObjectMapping(object_type).name)
    else:
        return Object


def map_objects_list(connection: "Connection", objects_list: List):
    return [
        map_to_object(obj.get('type'), obj.get('subtype')).from_dict(source=obj,
                                                                     connection=connection)
        for obj in objects_list
    ]

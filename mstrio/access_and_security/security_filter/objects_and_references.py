from typing import Optional

from mstrio.utils.helper import Dictable


class ObjectInformation(Dictable):
    """An object that contains all of the type-neutral information stored in the
    metadata about an object.

    Attributes:
        id (string): a globally unique identifier used to distinguish between
            metadata objects within the same project.
        subtype (string): string literal used to identify the type of a metadata
            object.
        name (string): the name of the metadata object.
        is_embedded (boolean): True indicates that the target object of this
            reference is embedded within this object. Alternatively if this
            object is itself embedded, then it means that the target object is
            embedded in the same container as this object.
        description (string): user supplied description of this object.
        date_created (string): the date/time at which this object was first
            saved into the metadata.
        date_modified (string): the date/time at which this object was last
            saved into the metadata.
        destination_folder_id (string): id of a folder in which the object is
            stored.
        version_id (string): the version number this object is currently
            carrying.
        path (string): the path of this object
        acl (list of objects): an array of access control entry objects. Taken
            together these objects specify which users are permitted to perform
            which actions on this object.
        primary (string): the primary locale of the object, in the IETF BCP 47
            language tag format, such as "en-US".
    """
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, object_id: Optional[str] = None, sub_type: Optional[str] = None,
                 name: Optional[str] = None, is_embedded: Optional[bool] = None,
                 description: Optional[str] = None, date_created: Optional[str] = None,
                 date_modified: Optional[str] = None, destination_folder_id: Optional[str] = None,
                 version_id: Optional[str] = None, path: Optional[str] = None,
                 acl: Optional[dict] = None, primary_locale: Optional[str] = None):
        self.object_id = object_id
        self.sub_type = sub_type
        self.name = name
        self.is_embedded = is_embedded
        self.description = description
        self.date_created = date_created
        self.date_modified = date_modified
        self.destination_folder_id = destination_folder_id
        self.version_id = version_id
        self.path = path
        self.acl = acl
        self.primary_locale = primary_locale


class ObjectReference(Dictable):
    """Information about an object referenced within the specification of
    another object. An object reference typically contains only enough fields
    to uniquely identify the referenced objects.

    object_id (string): a globally unique identifier used to distinguish between
        metadata objects within the same project.
    sub_type (string): string literal used to identify the type of a metadata
        object
    name (string): the name of the metadata object.
    is_embedded (boolean): True indicates that the target object of this
        reference is embedded within this object. Alternatively if this
        object is itself embedded, then it means that the target object is
        embedded in the same container as this object.
    """
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, object_id: str, sub_type: str, name: Optional[str] = None,
                 is_embedded: Optional[bool] = None):
        self.object_id = object_id
        self.sub_type = sub_type
        self.name = name
        self.is_embedded = is_embedded


class _ObjectReferenceWithType(ObjectReference):
    SUB_TYPE = ""
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, object_id: str, name: Optional[str] = None,
                 is_embedded: Optional[bool] = None):
        super().__init__(object_id, self.SUB_TYPE, name, is_embedded)


class AttributeRef(_ObjectReferenceWithType):
    _DELETE_NONE_VALUES_RECURSION = True

    SUB_TYPE = "attribute"


class AttributeFormSystemRef(_ObjectReferenceWithType):
    _DELETE_NONE_VALUES_RECURSION = True

    SUB_TYPE = "attribute_form_system"


class AttributeFormNormalRef(_ObjectReferenceWithType):
    _DELETE_NONE_VALUES_RECURSION = True

    SUB_TYPE = "attribute_form_normal"


class AttributeElement(Dictable):
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, element_id: str, display: str, attribute: Optional[AttributeRef] = None):
        self.element_id = element_id
        self.display = display
        self.attribute = attribute


class ElementPromptRef(_ObjectReferenceWithType):
    _DELETE_NONE_VALUES_RECURSION = True

    SUB_TYPE = "prompt"


class FilterRef(_ObjectReferenceWithType):
    _DELETE_NONE_VALUES_RECURSION = True

    SUB_TYPE = "filter"

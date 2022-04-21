from builtins import type as get_type
from enum import auto
from typing import Optional, Union

from mstrio.access_and_security.security_filter import ObjectInformation, ObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable

# TODO maybe enhance Qualification of security filter definition
# with given objects


class TokenTextType(AutoName):
    END_OF_TEXT = auto()
    ERROR = auto()
    UNKNOWN = auto()
    EMPTY = auto()
    CHARACTER = auto()
    LITERAL = auto()
    IDENTIFIER = auto()
    STRING_LITERAL = auto()
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    GUID = auto()
    OBJECT_REFERENCE = auto()
    COLUMN_REFERENCEE = auto()
    OBJECT_AT_FORM = auto()
    FUNCTION = auto()
    KEYWORD = auto()
    OTHER = auto()


class TokenLevel(AutoName):
    CLIENT = auto()
    LEXED = auto()
    RESOLVED = auto()
    PARSED = auto()


class TokenState(AutoName):
    ERROR = auto()
    INITIAL = auto()
    OKAY = auto()


class ParserToken(Dictable):
    """Structure that represents a fragment of text that should be handled as
    one entity when parsing.

    The expression parser annotates the text it parses by converting it into an
    array of token objects. These objects are used for several purposes:
        - they allow us to record extra information (generally the identity of
          an object) that is not explicitly shown in the raw text. Thus once we
          have disambiguated a name, it is not necessary to do so again.
        - they permit a GUI to reformat the text (using colour, type-face etc.)
          to make it easier to understand the expression.
        - they allow the parser to report the location of parse errors within
          the raw text.

    Attributes:
        value (string): the raw text represented by this token.
        type (enum): enumeration constant that classifies the text within this
            token
        level (enum): describe the amount of processing performed on this
            parser token
        state (enum): whether token is an error or not
        target (object): if the token represents an object, provide information
            about the object
        attribute_form (object): if the token represents an attribute form in
            the context of an object (say `City@DESC`) then provide information
            about the attribute form.
    """
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, value: str, type: Optional[Union[TokenTextType, str]] = None,
                 level: Optional[Union[TokenLevel, str]] = None,
                 state: Optional[Union[TokenState, str]] = None,
                 target: Optional[ObjectInformation] = None,
                 attribute_form: Optional[ObjectReference] = None):
        self.value = value
        self.type = type if isinstance(
            type, (TokenTextType, get_type(None))
        ) else TokenTextType(type)
        self.level = level if isinstance(
            level, (TokenLevel, get_type(None))
        ) else TokenLevel(level)
        self.state = state if isinstance(
            state, (TokenState, get_type(None))
        ) else TokenState(state)
        self.target = target
        self.attribute_form = attribute_form

    _FROM_DICT_MAP = {
        "type": TokenTextType,
        "level": TokenLevel,
        "state": TokenState,
        "target": ObjectInformation.from_dict,
        "attribute_form": ObjectReference.from_dict
    }

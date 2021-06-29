from enum import Enum
from mstrio.utils.helper import Dictable
from typing import Optional

from mstrio.access_and_security.security_filter import ObjectReference, ObjectInformation

# TODO maybe enhance Qualification of security filter definition
# with given objects


class TokenTextType(Enum):
    END_OF_TEXT = 'end_of_text'
    ERROR = 'error'
    UNKNOWN = 'unknown'
    EMPTY = 'empty'
    CHARACTER = 'character'
    LITERAL = 'literal'
    IDENTIFIER = 'identifier'
    STRING_LITERAL = 'string_literal'
    INTEGER = 'integere'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    GUID = 'guid'
    OBJECT_REFERENCE = 'object_reference'
    COLUMN_REFERENCEE = 'column_reference'
    OBJECT_AT_FORM = 'object_at_form'
    FUNCTION = 'function'
    KEYWORD = 'keyword'
    OTHER = 'other'


class TokenLevel(Enum):
    CLIENT = 'client'
    LEXED = 'lexed'
    RESOLVED = 'resolved'
    PARSED = 'parsed'


class TokenState(Enum):
    ERROR = 'error'
    INITIAL = 'initial'
    OKAY = 'okay'


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

    def __init__(self, value: str, type: Optional[TokenTextType] = None,
                 level: Optional[TokenLevel] = None, state: Optional[TokenState] = None,
                 target: Optional[ObjectInformation] = None,
                 attribute_form: Optional[ObjectReference] = None):
        self.value = value
        self.type = type
        self.level = level
        self.state = state
        self.target = target
        self.attrtibute_form = attribute_form

    _FROM_DICT_MAP = {
        "type": TokenTextType,
        "level": TokenLevel,
        "state": TokenState,
        "target": ObjectInformation.from_dict,
        "attribute_form": ObjectReference.from_dict
    }

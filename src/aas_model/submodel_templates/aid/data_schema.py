"""Data schemas: the TD DataSchema (TD 1.1 §5.3.2.1) as AID writes it, plus
the terms AID marks EXTERNAL (docs/aid-extension.md §3.6). The same structure
at every depth: a property affordance, an action's input and output, an
event's payloads, an object member, an array's ``items``, a ``oneOf``
alternative and an additional response's schema."""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from aas_pydantic import Property, SubmodelElementCollection, SubmodelElementList
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    properties_json_schema as _BaseSchemaProperties,
    property_name_json_schema as _BaseDataSchema,
)

from aas_model.constants import (
    AID_WOT_CONTENT_ENCODING, AID_WOT_CONTENT_MEDIA_TYPE, AID_WOT_DATA_SCHEMA, AID_WOT_EXCLUSIVE_MAXIMUM,
    AID_WOT_EXCLUSIVE_MINIMUM, AID_WOT_FORMAT, AID_WOT_ITEMS, AID_WOT_MULTIPLE_OF, AID_WOT_ONE_OF,
    AID_WOT_PATTERN, AID_WOT_READ_ONLY, AID_WOT_REQUIRED, AID_WOT_WRITE_ONLY,
)
from aas_model.submodel_templates.aid.elements import StringList


class Required(StringList):
    """``required`` (jsonschema:required) of an object schema: the names of
    the members that must be present. A name is the member's JSON name, its
    ``key`` (its idShort when it has no ``key``)."""
    id_short: AasIdString = "required"
    semantic_id: str = AID_WOT_REQUIRED
    description: str = "Names of the members of this object that must be present."
    type_value_list_element: str = "Property"
    value_type_list_element: str = "xs:string"


class ExclusiveMinimum(Property):
    id_short: AasIdString = "exclusiveMinimum"
    semantic_id: str = AID_WOT_EXCLUSIVE_MINIMUM
    description: str = "Values must be greater than this bound (number or integer schemas)."
    value_type: str = "xs:double"


class ExclusiveMaximum(Property):
    id_short: AasIdString = "exclusiveMaximum"
    semantic_id: str = AID_WOT_EXCLUSIVE_MAXIMUM
    description: str = "Values must be less than this bound (number or integer schemas)."
    value_type: str = "xs:double"


class MultipleOf(Property):
    id_short: AasIdString = "multipleOf"
    semantic_id: str = AID_WOT_MULTIPLE_OF
    description: str = "Values must be a multiple of this positive number (number or integer schemas)."
    value_type: str = "xs:double"


class Pattern(Property):
    id_short: AasIdString = "pattern"
    semantic_id: str = AID_WOT_PATTERN
    description: str = "ECMA-262 regular expression a string value must match."
    value_type: str = "xs:string"


class SchemaFormat(Property):
    """``format`` of a data schema (named apart from AID's security ``Format``)."""
    id_short: AasIdString = "format"
    semantic_id: str = AID_WOT_FORMAT
    description: str = "Format of a string value (JSON Schema format, e.g. date-time, uuid)."
    value_type: str = "xs:string"


class ContentEncoding(Property):
    id_short: AasIdString = "contentEncoding"
    semantic_id: str = AID_WOT_CONTENT_ENCODING
    description: str = "Encoding of binary content in a string value (e.g. base64)."
    value_type: str = "xs:string"


class ContentMediaType(Property):
    id_short: AasIdString = "contentMediaType"
    semantic_id: str = AID_WOT_CONTENT_MEDIA_TYPE
    description: str = "Media type of the content of a string value (e.g. image/png)."
    value_type: str = "xs:string"


class ReadOnly(Property):
    id_short: AasIdString = "readOnly"
    semantic_id: str = AID_WOT_READ_ONLY
    description: str = "The value cannot be written. Default false."
    value_type: str = "xs:boolean"


class WriteOnly(Property):
    id_short: AasIdString = "writeOnly"
    semantic_id: str = AID_WOT_WRITE_ONLY
    description: str = "The value cannot be read. Default false."
    value_type: str = "xs:boolean"


class DataSchemaTerms(SubmodelElementCollection):
    """The TD DataSchema terms AID marks EXTERNAL, added to every data schema.

    A mixin listed *after* the AID class it extends: pydantic merges each
    base's whole field set, so listed first it would replace the AID class's
    idShort, semanticId and description with the bare collection's."""
    readOnly: Optional[ReadOnly] = None
    writeOnly: Optional[WriteOnly] = None
    required: Optional[Required] = None
    oneOf: Optional[OneOf] = None
    exclusiveMinimum: Optional[ExclusiveMinimum] = None
    exclusiveMaximum: Optional[ExclusiveMaximum] = None
    multipleOf: Optional[MultipleOf] = None
    pattern: Optional[Pattern] = None
    format: Optional[SchemaFormat] = None
    contentEncoding: Optional[ContentEncoding] = None
    contentMediaType: Optional[ContentMediaType] = None


class DmpDataSchema(_BaseDataSchema, DataSchemaTerms):
    """A TD DataSchema: AID's data schema (``type``, ``title``, ``enum``,
    ``const``, ``default``, ``unit``, the ``min_max`` / ``lengthRange`` /
    ``itemsRange`` Ranges) with the :class:`DataSchemaTerms`; ``items`` and
    ``properties`` hold full data schemas, so nesting is unrestricted."""
    items: Optional[DmpItems] = None
    properties: Optional[DmpSchemaProperties] = None


class DmpItems(DmpDataSchema):
    """``items`` (jsonschema:items): the schema of every element of an array —
    a full data schema, so arrays of objects and of arrays are described.
    (AID's own ``items`` is a leaf schema; the idShort and semanticId are the
    same.) TD's other form, an array of schemas per position, is not used."""
    id_short: AasIdString = "items"
    semantic_id: str = AID_WOT_ITEMS
    description: str = "Data schema of the elements of an array."


class DmpSchemaProperties(_BaseSchemaProperties):
    """``properties`` of an object schema (member name → data schema)."""
    property_name: Dict[str, DmpDataSchema] = {}


class DmpOneOfBranch(DmpDataSchema):
    """One alternative of a ``oneOf``."""
    id_short: AasIdString = "branch"
    semantic_id: str = AID_WOT_DATA_SCHEMA
    description: str = "One alternative data schema."


class OneOf(SubmodelElementList):
    """``oneOf`` (jsonschema:oneOf): a value is valid against exactly one of
    these data schemas. A nullable value is ``oneOf`` its schema and
    ``{type: null}``."""
    id_short: AasIdString = "oneOf"
    semantic_id: str = AID_WOT_ONE_OF
    description: str = "Alternative data schemas; a value is valid against exactly one."
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = AID_WOT_DATA_SCHEMA
    item_type: ClassVar = DmpOneOfBranch
    value: List[DmpOneOfBranch] = []


# The schemas refer to each other (items, properties and oneOf hold schemas).
for _model in (DataSchemaTerms, DmpDataSchema, DmpItems, DmpSchemaProperties, DmpOneOfBranch, OneOf):
    _model.model_rebuild()

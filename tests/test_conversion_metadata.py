import os
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from basyx.aas import model
from basyx.aas.model import datatypes

from aas_pydantic import aas_model
from aas_pydantic.convert_aas_instance import (
    convert_file_to_pydantic_model,
    convert_blob_to_pydantic_model,
    convert_submodel_list_to_pydantic_model,
    get_submodel_element_value,
    _convert_basyx_reference_to_pydantic,
)
from aas_pydantic.convert_pydantic_model import (
    _make_basyx_reference,
    create_submodel_element,
)


def _external_reference(uri: str) -> model.ExternalReference:
    return model.ExternalReference(
        key=(model.Key(model.KeyTypes.GLOBAL_REFERENCE, uri),)
    )


class PropertyList(aas_model.SubmodelElementList):
    item_type: ClassVar = aas_model.Property


def test_qualifier_supplemental_and_referred_semantic_ids_round_trip():
    qualifier = model.Qualifier(
        type_="constraint",
        value_type=datatypes.String,
        value="active",
        value_id=_external_reference("urn:value-id"),
        semantic_id=_external_reference("urn:qualifier-semantic"),
    )
    ref = model.ModelReference(
        key=(model.Key(model.KeyTypes.SUBMODEL, "urn:submodel"),),
        type_=model.Submodel,
        referred_semantic_id=_external_reference("urn:referred-semantic"),
    )
    element = model.ReferenceElement(
        id_short="Reference",
        value=ref,
        qualifier=[qualifier],
        supplemental_semantic_id=[_external_reference("urn:supplemental")],
    )

    converted = get_submodel_element_value(element)
    assert converted.supplemental_semantic_ids == ["urn:supplemental"]
    assert converted.qualifiers[0].value_id == "urn:value-id"
    assert converted.qualifiers[0].semantic_id == "urn:qualifier-semantic"
    assert converted.value.referred_semantic_id == "urn:referred-semantic"

    rebuilt = create_submodel_element("Reference", converted)
    assert rebuilt.supplemental_semantic_id[0].key[0].value == "urn:supplemental"
    rebuilt_qualifier = next(iter(rebuilt.qualifier))
    assert rebuilt_qualifier.value_id.key[0].value == "urn:value-id"
    assert rebuilt.value.referred_semantic_id.key[0].value == "urn:referred-semantic"
    assert _convert_basyx_reference_to_pydantic(
        _make_basyx_reference(converted.value)
    ).referred_semantic_id == "urn:referred-semantic"


def test_submodel_element_list_metadata_round_trip():
    original = model.SubmodelElementList(
        id_short="Entries",
        type_value_list_element=model.Property,
        value_type_list_element=datatypes.Int,
        semantic_id_list_element=_external_reference("urn:item-semantic"),
        value=[model.Property(id_short=None, value_type=datatypes.Int, value=7)],
        order_relevant=False,
        supplemental_semantic_id=[_external_reference("urn:list-supplemental")],
    )

    converted = convert_submodel_list_to_pydantic_model(original, PropertyList)
    assert converted.semantic_id_list_element == "urn:item-semantic"
    assert converted.value_type_list_element == "xs:int"
    assert converted.type_value_list_element == "Property"
    assert converted.order_relevant is False
    assert converted.supplemental_semantic_ids == ["urn:list-supplemental"]

    rebuilt = create_submodel_element("Entries", converted)
    assert rebuilt.semantic_id_list_element.key[0].value == "urn:item-semantic"
    assert rebuilt.value_type_list_element is datatypes.Int
    assert rebuilt.type_value_list_element is model.Property
    assert rebuilt.order_relevant is False
    assert rebuilt.supplemental_semantic_id[0].key[0].value == "urn:list-supplemental"


def test_file_and_blob_qualifiers_and_supplemental_ids_round_trip():
    for element, converter in (
        (
            model.File(
                id_short="File",
                content_type="text/plain",
                value="data.txt",
                qualifier=[model.Qualifier("format", datatypes.String, "raw")],
                supplemental_semantic_id=[_external_reference("urn:file-supp")],
            ),
            convert_file_to_pydantic_model,
        ),
        (
            model.Blob(
                id_short="Blob",
                content_type="application/octet-stream",
                value=b"data",
                qualifier=[model.Qualifier("format", datatypes.String, "raw")],
                supplemental_semantic_id=[_external_reference("urn:blob-supp")],
            ),
            convert_blob_to_pydantic_model,
        ),
    ):
        converted = converter(element)
        rebuilt = create_submodel_element(element.id_short, converted)
        checked = get_submodel_element_value(rebuilt)
        assert checked.qualifiers[0].value == "raw"
        assert checked.supplemental_semantic_ids == [
            element.supplemental_semantic_id[0].key[0].value
        ]


def test_validation_is_not_disabled_by_optimized_python():
    script = """
from pydantic import ValidationError
from aas_pydantic import Key, ModelReference, Property

for constructor in (
    lambda: Property(id_short=""),
    lambda: ModelReference(key=(Key(type_="Property", value="urn:item"),)),
):
    try:
        constructor()
    except ValidationError:
        pass
    else:
        raise RuntimeError("invalid input was accepted")
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert result.returncode == 0, result.stderr

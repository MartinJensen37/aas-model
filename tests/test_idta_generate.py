import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import get_args

import pytest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "idta_generate.py"
SPEC = importlib.util.spec_from_file_location("idta_generate", GENERATOR_PATH)
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def test_field_name_preserves_safe_idshort_spelling():
    assert generator.field_name("ManufacturerName") == "ManufacturerName"
    assert generator.field_name("InterfaceTemplateForMQTT") == "InterfaceTemplateForMQTT"
    assert generator.field_name("Mode__00__") == "Mode"
    assert generator.field_name("in") == "in_"
    assert generator.field_name("2D-Name") == "_2D_Name"


def test_default_template_paths_exist_and_output_is_package_directory():
    assert generator.OUTPUT_ROOT == str(
        ROOT / "src" / "aas_pydantic" / "submodel_templates"
    )
    assert len(generator.TEMPLATES) == 8
    assert all((Path(generator.TEMPLATE_ROOT) / template).is_file()
               for template in generator.TEMPLATES)


def test_all_pinned_templates_emit_parseable_modules(tmp_path):
    for template in generator.TEMPLATES:
        generator.gen_template(
            str(Path(generator.TEMPLATE_ROOT) / template), str(tmp_path)
        )

    modules = list(tmp_path.glob("*.py"))
    assert len(modules) == len(generator.TEMPLATES)
    for module in modules:
        assert module.read_bytes() == (Path(generator.OUTPUT_ROOT) / module.name).read_bytes(), (
            f"Regeneration changed the checked-in {module.name}"
        )
        tree = ast.parse(module.read_text())
        if module.name == "asset_interfaces_description.py":
            forms = next(
                node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "forms"
            )
            fields = {
                node.target.id: ast.unparse(node.annotation)
                for node in forms.body
                if isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
            }
            assert fields["href"] == "Href"
            assert {
                "htv_methodName",
                "modv_function",
                "mqv_retain",
                "uav_browsePath",
                "iolv_method",
                "canv_offset",
            } <= fields.keys()
            assert all(
                fields[field].startswith("Optional[")
                for field in (
                    "htv_methodName",
                    "modv_function",
                    "mqv_retain",
                    "uav_browsePath",
                    "iolv_method",
                    "canv_offset",
                )
            )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib.util, sys; "
                "spec = importlib.util.spec_from_file_location('generated_template', sys.argv[1]); "
                "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                "expected = {'htv_methodName', 'modv_function', 'mqv_retain', "
                "'uav_browsePath', 'iolv_method', 'canv_offset'} "
                "if sys.argv[2] == 'aid' else set(); "
                "assert expected <= module.forms.model_fields.keys() if expected else True; "
                "assert module.forms.model_fields['href'].is_required() if expected else True; "
                "assert all(not module.forms.model_fields[field].is_required() for field in expected)",
                str(module),
                "aid" if module.name == "asset_interfaces_description.py" else "other",
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    [str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]
                ),
            },
        )
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("suffix", ["", "_forAASMetamodelV3.1"], ids=["AAS3.0", "AAS3.1"])
def test_contact_information_source_uses_standard_cardinality_qualifiers(tmp_path, suffix):
    source = (
        Path(generator.TEMPLATE_ROOT) / "Contact Information" / "1" / "0" / "2"
        / f"IDTA 02002-1-0-2_Template_ContactInformation{suffix}.json"
    )
    text = source.read_text(encoding="utf-8")
    assert '"type": "Multiplicity"' not in text
    assert text.count('"type": "SMT/Cardinality"') == 36
    generator.gen_template(str(source), str(tmp_path))

    verification = """
import importlib.util
import sys
from typing import get_origin

spec = importlib.util.spec_from_file_location("generated_contact_information", sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

assert get_origin(module.ContactInformations.model_fields["ContactInformation"].annotation) is dict
for name in ("Language", "IPCommunication"):
    assert get_origin(module.ContactInformation.model_fields[name].annotation) is dict
for name in (
    "RoleOfContactPerson", "Company", "Department", "Street", "Zipcode",
    "CityTown", "NationalCode", "Phone", "Fax", "Email", "AddressOfAdditionalLink",
):
    assert not module.ContactInformation.model_fields[name].is_required(), name
for container, child in (
    (module.Phone, "TelephoneNumber"), (module.Fax, "FaxNumber"),
    (module.Email, "EmailAddress"), (module.IPCommunication, "AddressOfAdditionalLink"),
):
    assert container.model_fields[child].is_required(), child

contact = module.ContactInformation(
    id_short="Manufacturer", Street=module.Street(value={"en": "Example Street"}),
)
model = module.ContactInformations(id_short="Contacts", ContactInformation={
    "Manufacturer": contact, "Service": module.ContactInformation(id_short="Service"),
})
restored = module.ContactInformations.model_validate_json(model.model_dump_json())
assert set(restored.ContactInformation) == {"Manufacturer", "Service"}
assert restored.ContactInformation["Manufacturer"].Street.value == {"en": "Example Street"}
assert restored.ContactInformation["Service"].RoleOfContactPerson is None
"""
    result = subprocess.run(
        [sys.executable, "-c", verification, str(tmp_path / "contact_informations.py")],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    assert result.returncode == 0, result.stderr


def test_repeated_concept_fields_merge_by_presence_and_cardinality(tmp_path):
    def field(name, cardinality):
        return {
            "modelType": "Property",
            "idShort": name,
            "qualifiers": [{"type": "SMT/Cardinality", "value": cardinality}],
        }

    def interface(name, protocol_field):
        return {
            "modelType": "SubmodelElementCollection",
            "idShort": name,
            "semanticId": {"keys": [{"value": f"urn:interface:{name}"}]},
            "value": [{
                "modelType": "SubmodelElementCollection",
                "idShort": "forms",
                "semanticId": {"keys": [{"value": "urn:shared:forms"}]},
                "value": [field("href", "One"), field(protocol_field, "One")],
            }],
        }

    template_path = tmp_path / "variants.json"
    template_path.write_text(json.dumps({
        "submodels": [{
            "modelType": "Submodel",
            "idShort": "SharedForms",
            "submodelElements": [
                interface("MqttInterface", "mqv_qos"),
                interface("HttpInterface", "htv_methodName"),
            ],
        }]
    }))

    output_dir = tmp_path / "generated-variants"
    generator.gen_template(str(template_path), str(output_dir))
    generated = (output_dir / "shared_forms.py").read_text()
    tree = ast.parse(generated)
    forms = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "forms"
    )
    fields = {
        node.target.id: (ast.unparse(node.annotation), node.value)
        for node in forms.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert fields["href"][0] == "Property"
    assert fields["mqv_qos"][0] == "Optional[Property]"
    assert fields["htv_methodName"][0] == "Optional[Property]"
    assert all(fields[name][1] is not None for name in ("mqv_qos", "htv_methodName"))


def test_repeated_concept_with_conflicting_field_types_fails():
    with pytest.raises(ValueError, match=r"Incompatible field types for Forms\.value"):
        generator.merge_fields("Forms", [
            [generator.FieldSpec("value", ("Property",), shape="list")],
            [generator.FieldSpec("value", ("ReferenceElement",), shape="list")],
        ])


def test_field_specs_merge_without_parsing_rendered_source():
    first = generator.FieldSpec("child", ("Original",), required=True)
    second = generator.FieldSpec("child", ("Variant",))
    merged = generator.merge_fields(
        "Parent", [[first], [second]], compatible=lambda a, b: True,
    )
    assert merged == [generator.FieldSpec("child", ("Original", "Variant"))]
    assert merged[0].render(set()) == "    child: Optional[Union[Original, Variant]] = None"

    with pytest.raises(ValueError, match="Incompatible repeatable defaults"):
        generator.merge_fields("Parent", [
            [generator.FieldSpec("items", ("Item",), shape="map", minimum=1)],
            [generator.FieldSpec("items", ("Item",), shape="map")],
        ])


def test_generation_preserves_named_fields_and_source_provenance(tmp_path):
    template_path = tmp_path / "template.json"
    template_path.write_text(json.dumps({
        "submodels": [{
            "modelType": "Submodel",
            "idShort": "SampleSubmodel",
            "submodelElements": [{
                "modelType": "SubmodelElementCollection",
                "idShort": "InterfaceTemplateForMQTT",
                "semanticId": {"keys": [{"value": "urn:example:container"}]},
                "qualifiers": [{"type": "SMT/Cardinality", "value": "One"}],
                "value": [
                    {
                        "modelType": "Property",
                        "idShort": "ManufacturerName",
                        "qualifiers": [{
                            "type": "SMT/Cardinality", "value": "ZeroToOne"
                        }],
                    },
                    {
                        "modelType": "Property",
                        "idShort": "in",
                        "qualifiers": [{
                            "type": "SMT/Cardinality", "value": "ZeroToOne"
                        }],
                    },
                ],
            }],
        }]
    }))

    output_dir = tmp_path / "generated"
    generator.gen_template(str(template_path), str(output_dir))
    output_path = output_dir / "sample_submodel.py"
    generated = output_path.read_text()
    ast.parse(generated)

    assert "Source:" in generated
    assert generated.split("Source: ", 1)[1].splitlines()[0].endswith("template.json")
    assert "class InterfaceTemplateForMQTT(SubmodelElementCollection):" in generated
    assert "ManufacturerName: Optional[Property] = None" in generated
    assert 'in_: Optional[Property] = Field(default=None, json_schema_extra={"aas_id_short": "in"})' in generated
    assert "InterfaceTemplateForMQTT_t: TypeAlias = InterfaceTemplateForMQTT" in generated
    assert "InterfaceTemplateForMQTT: InterfaceTemplateForMQTT_t" in generated

    first_output = generated
    generator.gen_template(str(template_path), str(output_dir))
    assert output_path.read_text() == first_output


def _generate_fixture(tmp_path, children):
    source = tmp_path / "fixture.json"
    source.write_text(json.dumps({"submodels": [{
        "modelType": "Submodel", "idShort": "ReviewModel",
        "submodelElements": children,
    }]}))
    generator.gen_template(str(source), str(tmp_path))
    spec = importlib.util.spec_from_file_location(
        f"idta_fixture_{tmp_path.name.replace('-', '_')}",
        tmp_path / "review_model.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _element(name, kind="Property", sid=None, **extra):
    return {
        "modelType": kind, "idShort": name,
        "semanticId": {"keys": [{"value": sid or f"urn:{name}"}]},
        **extra,
    }


def test_sanitized_fields_keep_original_aas_id_short(tmp_path):
    module = _generate_fixture(tmp_path, [
        _element("in", valueType="xs:string"),
        _element("Has-Hyphen"),
    ])
    model = module.ReviewModel(id_short="ReviewModel", in_={"value": "header"}, Has_Hyphen={"value": "yes"})
    assert model.in_.id_short == "in"
    assert model.Has_Hyphen.id_short == "Has-Hyphen"


def test_aid_keyword_field_round_trips_with_original_id_short():
    from aas_pydantic.convert_pydantic_model import create_submodel_element
    from aas_pydantic.convert_aas_instance import _container_element_to_pydantic
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        In, Scheme, basic_sc,
    )

    security = basic_sc(scheme=Scheme(value="basic"), in_=In(value="header"))
    basyx = create_submodel_element("basic_sc", security)
    assert {child.id_short for child in basyx.value} == {"scheme", "in"}
    assert _container_element_to_pydantic(basyx, basic_sc).in_.id_short == "in"


def test_required_repeated_elements_can_be_validated_before_publishing(tmp_path):
    from aas_pydantic import validate_idta_cardinality

    module = _generate_fixture(tmp_path, [_element(
        "Items", "Property", qualifiers=[
            {"type": "SMT/Cardinality", "value": "TwoToMany"}
        ]
    )])
    incomplete = module.ReviewModel(id_short="ReviewModel")
    with pytest.raises(ValueError, match="ReviewModel.Items requires at least 2 entries"):
        validate_idta_cardinality(incomplete)
    with pytest.raises(ValueError, match="ReviewModel.Items requires at least 2 entries"):
        validate_idta_cardinality(module.ReviewModel(
            id_short="ReviewModel", Items={"First": module.Items()}
        ))
    validate_idta_cardinality(module.ReviewModel(id_short="ReviewModel", Items={
        "First": module.Items(), "Second": module.Items(),
    }))


def test_list_declarations_not_example_defaults_are_authoritative(tmp_path):
    from aas_pydantic.convert_aas_instance import convert_submodel_list_to_pydantic_model
    from aas_pydantic.convert_pydantic_model import create_submodel_element

    module = _generate_fixture(tmp_path, [_element(
        "Readings", "SubmodelElementList", orderRelevant=False,
        typeValueListElement="Property", valueTypeListElement="xs:int",
        semanticIdListElement={"keys": [{"value": "urn:item"}]},
        value=[{"modelType": "Property", "valueType": "xs:int"}],
    )])
    sml = module.Readings(value=[{"value": "4"}])
    assert sml.type_value_list_element == "Property"
    assert sml.value_type_list_element == "xs:int"
    assert sml.semantic_id_list_element == "urn:item"
    assert sml.order_relevant is False
    assert sml.value[0].value_type == "xs:int"
    exported = create_submodel_element("Readings", sml)
    assert exported.value_type_list_element.__name__ == "Int"
    assert exported.order_relevant is False
    assert exported.semantic_id_list_element.key[0].value == "urn:item"
    restored = convert_submodel_list_to_pydantic_model(exported, module.Readings)
    assert restored.value_type_list_element == "xs:int"
    assert restored.value[0].value_type == "xs:int"


def test_distinct_leaf_metadata_does_not_share_a_class(tmp_path):
    module = _generate_fixture(tmp_path, [
        _element("First", "SubmodelElementCollection", value=[
            _element("Attachment", "File", sid="urn:attachment", contentType="application/pdf")
        ]),
        _element("Second", "SubmodelElementCollection", value=[
            _element("Attachment", "File", sid="urn:attachment", contentType="image/png")
        ]),
    ])
    first = module.First.model_fields["Attachment"].annotation
    second = module.Second.model_fields["Attachment"].annotation
    assert first in get_args(second)
    assert first.model_fields["content_type"].default == "application/pdf"
    assert any(cls.model_fields["content_type"].default == "image/png" for cls in get_args(second))


def test_class_name_conflicts_with_generic_leaf_keep_semantics(tmp_path):
    module = _generate_fixture(tmp_path, [_element(
        "File", "File", sid="urn:attachment", contentType="text/csv"
    )])
    leaf = get_args(module.ReviewModel.model_fields["File"].annotation)[0]
    assert leaf.model_fields["semantic_id"].default == "urn:attachment"
    assert leaf.model_fields["content_type"].default == "text/csv"


def test_repeated_disambiguated_leaf_uses_one_definition(tmp_path):
    def child():
        return _element("Label", sid="urn:second-label")

    module = _generate_fixture(tmp_path, [
        _element("First", "SubmodelElementCollection", value=[
            _element("Label", sid="urn:first-label")
        ]),
        _element("Second", "SubmodelElementCollection", value=[child()]),
        _element("Wrapper", "SubmodelElementCollection", value=[
            _element("Second", "SubmodelElementCollection", value=[child()])
        ]),
    ])
    assert module.Second.model_fields["Label"].annotation is module.Wrapper.model_fields["Second"].annotation.model_fields["Label"].annotation


def test_relationship_defaults_are_references_not_tuples(tmp_path):
    reference = {"type": "ExternalReference", "keys": [
        {"type": "GlobalReference", "value": "urn:target"}
    ]}
    module = _generate_fixture(tmp_path, [_element(
        "Connects", "RelationshipElement", first=reference, second=reference
    )])
    assert module.Connects().first.key[0].value == "urn:target"


def test_invalid_class_and_field_names_fail_with_context(tmp_path):
    with pytest.raises(ValueError, match="Invalid class name.*class"):
        _generate_fixture(tmp_path, [_element("class", "SubmodelElementCollection")])
    with pytest.raises(ValueError, match="reserved.*semantic_id"):
        _generate_fixture(tmp_path, [_element("semantic_id")])


def test_unknown_element_types_are_not_silently_properties(tmp_path):
    with pytest.raises(ValueError, match="BasicEventElement"):
        _generate_fixture(tmp_path, [_element("Event", "BasicEventElement")])


def test_same_name_semantic_id_with_different_element_kinds_fails(tmp_path):
    with pytest.raises(ValueError, match="Duplicate or colliding idShorts.*Item"):
        _generate_fixture(tmp_path, [
            _element("Item", sid="urn:item"),
            _element("Item", "SubmodelElementCollection", sid="urn:item", value=[]),
        ])

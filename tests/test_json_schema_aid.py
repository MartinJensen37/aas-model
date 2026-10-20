"""JSON Schema keywords mirrored by AID datapoints and qualifiers."""

import json
from hashlib import sha256

import pytest

from aas_model._serde import parse_submodel_dict
from aas_model.json_schema_aid import (
    datapoint_from_schema,
    load_schema,
    populate_datapoint,
    schema_from_datapoint,
)
from aas_model.submodel_templates.aid import (
    DmpActionInput,
    DmpActionOutput,
    DmpAssetInterfacesDescription,
    DmpProperty,
)
from aas_model.testing import build_aid, mqtt_interface
from aas_pydantic import Qualifier

from test_serde import _roundtrip


def test_schema_required_fields_keep_authored_order_when_resolving_allof(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({
        "allOf": [
            {"type": "object", "required": ["Beta", "Alpha"]},
            {"type": "object", "required": ["Gamma", "Alpha"]},
        ],
        "required": ["Omega", "Beta"],
    }), encoding="utf-8")

    assert load_schema(str(path))["required"] == ["Beta", "Alpha", "Gamma", "Omega"]


def test_action_input_and_output_round_trip_supported_keywords():
    schema = {
        "type": "object",
        "title": "Command",
        "description": "The wire payload",
        "properties": {
            "Uuid": {"type": "string", "const": "a,b", "default": "a,b",
                     "minLength": 1, "maxLength": 36},
            "Speed": {"type": "number", "minimum": 0.0, "maximum": 10.5,
                      "unit": "m/s", "enum": [0.0, 2.5, 10.5]},
            "Status": {"type": "boolean", "default": False},
            "Sequence": {"type": "integer", "minimum": 1, "maximum": 9},
            "Options": {
                "type": "object",
                "properties": {
                    "Target": {"type": "string", "enum": ["near", "far"]},
                    "Attempts": {"type": "integer", "default": 2},
                },
                "required": ["Target"],
            },
            "Samples": {"type": "array", "minItems": 1, "maxItems": 4,
                        "items": {"type": "number", "minimum": -2,
                                  "maximum": 3, "default": 0}},
        },
        "required": ["Uuid", "Speed", "Options"],
    }
    for cls in (DmpActionInput, DmpActionOutput):
        dp = datapoint_from_schema(schema, cls=cls)
        assert schema_from_datapoint(dp) == schema
        assert dp.qualifiers == [], "required is a data schema element, not a qualifier"
        assert [name.value for name in dp.required.value] == ["Uuid", "Speed", "Options"]
        assert schema_from_datapoint(dp.properties.property_name["Options"])[
            "required"] == ["Target"]
        assert schema_from_datapoint(dp.properties.property_name["Uuid"])[
            "type"] == "string"


def test_required_is_replaced_on_repopulation_and_other_qualifiers_stay():
    prop = DmpProperty()
    prop.qualifiers = [Qualifier(type_="Custom", value="keep")]
    populate_datapoint(prop, {"type": "object", "required": ["part,one"],
                              "properties": {"part,one": {"type": "null"}}})
    assert schema_from_datapoint(prop) == {
        "type": "object", "required": ["part,one"],
        "properties": {"part,one": {"type": "null"}},
    }
    populate_datapoint(prop, {"type": "object", "required": [],
                              "properties": {"part,one": {"type": "null"}}})
    assert [q.type_ for q in prop.qualifiers] == ["Custom"]
    assert "required" not in schema_from_datapoint(prop), "an empty required list requires nothing"


def test_unrepresentable_keywords_fail_instead_of_vanishing():
    schema = {
        "type": "object", "required": ["Name"], "additionalProperties": False,
        "properties": {"Name": {"type": "string", "pattern": "^x", "format": "email"}},
    }
    with pytest.raises(ValueError, match="additionalProperties"):
        datapoint_from_schema(schema, cls=DmpActionInput)
    dp = datapoint_from_schema(schema, cls=DmpActionInput, ignore={"additionalProperties"},
                               schema_url="https://example.test/schema.json")
    assert schema_from_datapoint(dp) == {
        "type": "object", "required": ["Name"],
        "properties": {"Name": {"type": "string", "pattern": "^x", "format": "email"}},
    }


def test_qualifiers_survive_aas_json_serialization_and_parse():
    aid = build_aid(mqtt=mqtt_interface("mqtt://broker.example:1883/"))
    action = aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.actions.property_name
    from aas_model.resource_template.asset_interfaces_description import (
        mqtt_action, mqtt_property,
    )

    action["Send"] = mqtt_action(
        "Send", input_schema={"type": "object", "required": ["Uuid"],
                              "properties": {"Uuid": {"type": "string"},
                                             "Nested": {"type": "object",
                                                        "required": ["Count"],
                                                        "properties": {"Count": {
                                                            "type": "integer"}}}}},
        output_schema={"type": "object", "required": ["State"],
                       "properties": {"State": {"type": "string"}}},
    )
    aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.properties.property_name[
        "Status"
    ] = mqtt_property("Status", "/DATA/Status", schema={
        "type": "object", "title": "Status", "required": ["Mode"],
        "properties": {"Mode": {"type": "string"}},
    })
    document = _roundtrip(aid)
    restored = parse_submodel_dict(json.loads(json.dumps(document)),
                                   DmpAssetInterfacesDescription)
    back = restored.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.actions.property_name["Send"]
    assert schema_from_datapoint(back.input) == {
        "type": "object", "required": ["Uuid"],
        "properties": {"Uuid": {"type": "string"},
                       "Nested": {"type": "object", "required": ["Count"],
                                  "properties": {"Count": {"type": "integer"}}}},
    }
    assert schema_from_datapoint(back.output) == {
        "type": "object", "required": ["State"],
        "properties": {"State": {"type": "string"}},
    }
    prop = restored.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.properties.property_name["Status"]
    # readOnly is a DataSchema term (TD): the observed MQTT property is not writable.
    assert schema_from_datapoint(prop) == {
        "type": "object", "title": "Status", "required": ["Mode"], "readOnly": True,
        "properties": {"Mode": {"type": "string"}},
    }


def test_json_scalar_consts_and_arbitrary_member_names_serialize_and_round_trip():
    from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
    from aas_model.resource_template.asset_interfaces_description import mqtt_action

    schema = {
        "type": "object",
        "required": ["part,one"],
        "properties": {
            "part,one": {"type": "string", "const": "literal,value"},
            "enabled?": {"type": "boolean", "const": True},
            "precision": {"type": "number", "const": 1.25},
        },
    }
    aid = build_aid(mqtt=mqtt_interface("mqtt://broker.example:1883/"))
    actions = aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.actions
    actions.property_name["Send"] = mqtt_action("Send", input_schema=schema)

    document = _roundtrip(aid)
    serialized_text = json.dumps(document)
    assert '"valueType": "xs:string"' in serialized_text
    assert '"valueType": "xs:boolean"' in serialized_text
    assert '"valueType": "xs:double"' in serialized_text
    part_alias = "member_" + sha256(b"part,one").hexdigest() + "_0"
    enabled_alias = "member_" + sha256(b"enabled?").hexdigest() + "_1"
    assert f'"idShort": "{part_alias}"' in serialized_text
    assert f'"idShort": "{enabled_alias}"' in serialized_text

    restored = parse_submodel_dict(document, DmpAssetInterfacesDescription)
    restored_input = restored.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name["Send"].input
    assert schema_from_datapoint(restored_input) == schema


@pytest.mark.parametrize("bound", [0.5, -1.25])
@pytest.mark.parametrize("keyword", ["minimum", "maximum"])
def test_fractional_integer_bounds_are_rejected_instead_of_truncated(keyword, bound):
    with pytest.raises(ValueError, match=rf"integer {keyword}=.*cannot represent"):
        datapoint_from_schema({"type": "integer", keyword: bound})

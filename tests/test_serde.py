"""Tests for aas_model: AAS-JSON -> shared-model reverse parsing (ADR-016).

These lock the management node's parse to the same models the registration
service authors, using the real BaSyx REST fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

from aas_model._serde import parse_submodel_dict
from aas_model.submodel_templates import Aimc
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription

HERE = Path(__file__).parent


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def test_aimc_reverse_parses_to_shared_model():
    model = parse_submodel_dict(_load("data_aimc.json"), Aimc)
    assert isinstance(model, Aimc)
    mcs = model.MappingConfigurations.value
    assert len(mcs) == 5
    # The Transformation blob (Lua) is preserved.
    assert mcs[0].Transformation is not None
    assert mcs[0].Sources.value and mcs[0].Sinks.value


def test_aid_reverse_parses_to_shared_model_with_mqtt_actions():
    model = parse_submodel_dict(_load("data_aid.json"), DmpAssetInterfacesDescription)
    assert isinstance(model, DmpAssetInterfacesDescription)
    assert model.InterfaceTemplateForMQTT["interface_mqtt"] is not None
    im = model.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata
    actions = list(im.actions.property_name.keys())
    props = list(im.properties.property_name.keys())
    # The registration-service MQTT action extensions round-trip.
    assert {"Halt", "Occupy", "Release", "Stoppering"} <= set(actions)
    assert "StationState" in props


def test_round_trip_preserves_semantic_id():
    m = parse_submodel_dict(_load("data_aimc.json"), Aimc)
    assert m.semantic_id == (
        "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
    )


def test_aimc_response_sources_and_sinks_round_trip():
    from aas_model.resource_template.asset_interfaces_mapping_configuration import (
        mapping_configuration, response_sink, response_source, source, sink,
    )
    from aas_model.testing import aimc_ref
    from aas_model.resource_template import ResourceTypeAAS
    from aas_model.submodel_templates import AimcMappingConfigurations
    from aas_model.constants import BASE_URL
    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    from basyx.aas.adapter.json import json_serialization

    action_output = aimc_ref(
        "{aas_id}/submodels/AssetInterfacesDescription", "interface_mqtt",
        "InteractionMetadata", "actions", "Halt", "output", "State")
    operation = aimc_ref(
        "{aas_id}/submodels/ControlComponentInstance", "Skills", "Halt",
        "operation")
    variables = aimc_ref("{aas_id}/submodels/Variables", "PackMLState")
    mapping = mapping_configuration(
        id_short="Halt",
        sources=[source("Halt", operation)],
        sinks=[sink("Halt", aimc_ref(
            "{aas_id}/submodels/AssetInterfacesDescription", "interface_mqtt",
            "InteractionMetadata", "actions", "Halt"))],
        transformation="function aimc_main(sources) return sources end",
        response_sources=[response_source("DeviceState", action_output)],
        response_sinks=[response_sink("PackMLState", variables)],
    )
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(
        value=[mapping]))
    asset = ResourceTypeAAS(
        id_short="RoundTrip", id=f"{BASE_URL}/aas/RoundTrip", asset_type="RoundTrip",
        asset_interfaces_mapping_configuration=aimc)
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")
    back = parse_submodel_dict(serialized, Aimc)

    response_mapping = back.MappingConfigurations.value[0]
    assert response_mapping.ResponseSources.value[0].SourceId.value == "DeviceState"
    assert response_mapping.ResponseSources.value[0].Source.value.key[-1].value == "State"
    assert response_mapping.ResponseSinks.value[0].SinkId.value == "PackMLState"
    assert response_mapping.ResponseSinks.value[0].Sink.value.key[-1].value == "PackMLState"


def test_aimc_response_endpoints_are_optional():
    from aas_model.testing import aimc_mapping
    from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
        SourcesItem as Source, SinksItem as Sink, Source as SourceReference,
        Sink as SinkReference, SourceId, SinkId,
    )
    from aas_pydantic import ModelReference, Key

    mapping = aimc_mapping(
        sources=[Source(Source=SourceReference(value=ModelReference(key=(
            Key(type_="Submodel", value="urn:source"),))), SourceId=SourceId(value="s"))],
        sinks=[Sink(Sink=SinkReference(value=ModelReference(key=(
            Key(type_="Submodel", value="urn:sink"),))), SinkId=SinkId(value="t"))],
    )
    assert mapping.ResponseSources is None
    assert mapping.ResponseSinks is None
    assert mapping.ExecutionSemantics is None


def test_aimc_execution_semantics_round_trip_and_authors_source_ids():
    from aas_model.testing import aimc_mapping
    from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
        SourcesItem as Source, SinksItem as Sink, Source as SourceReference,
        Sink as SinkReference, SourceId, SinkId,
    )
    from aas_pydantic import ModelReference, Key

    mapping = aimc_mapping(
        sources=[Source(Source=SourceReference(value=ModelReference(key=(
            Key(type_="Submodel", value="urn:source"),))), SourceId=SourceId(value="invoke"))],
        sinks=[Sink(Sink=SinkReference(value=ModelReference(key=(
            Key(type_="Submodel", value="urn:sink"),))), SinkId=SinkId(value="target"))],
        trigger_source_ids=["invoke", "position"],
    )
    semantics = mapping.ExecutionSemantics
    from aas_model.constants import AIMC_EXECUTION_SEMANTICS, AIMC_TRIGGER_SOURCE_IDS
    assert semantics.semantic_id == AIMC_EXECUTION_SEMANTICS
    trigger_ids = semantics.TriggerSourceIds
    assert trigger_ids.semantic_id == AIMC_TRIGGER_SOURCE_IDS
    assert trigger_ids.type_value_list_element == "Property"
    assert trigger_ids.value_type_list_element == "xs:string"
    assert [item.value for item in trigger_ids.value] == ["invoke", "position"]

    from aas_model.constants import BASE_URL
    from aas_model.resource_template import ResourceTypeAAS
    from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    from basyx.aas.adapter.json import json_serialization

    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(
        value=[mapping]))
    asset = ResourceTypeAAS(
        id_short="ExecutionSemanticsRoundTrip",
        id=f"{BASE_URL}/aas/ExecutionSemanticsRoundTrip",
        asset_type="ExecutionSemanticsRoundTrip",
        asset_interfaces_mapping_configuration=aimc,
    )
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")
    restored = parse_submodel_dict(serialized, Aimc)
    restored_ids = restored.MappingConfigurations.value[0].ExecutionSemantics.TriggerSourceIds
    assert [item.value for item in restored_ids.value] == ["invoke", "position"]


def test_resource_mapping_configuration_accepts_trigger_source_ids():
    from aas_model.resource_template.asset_interfaces_mapping_configuration import (
        mapping_configuration, source, sink, operation_ref, _variable_ref,
    )

    mapping = mapping_configuration(
        id_short="Triggered",
        sources=[source("invoke", operation_ref("Start"))],
        sinks=[sink("result", _variable_ref("PackMLState"))],
        transformation="function aimc_main(sources) return sources end",
        trigger_source_ids=["invoke"],
    )
    assert [item.value for item in mapping.ExecutionSemantics.TriggerSourceIds.value] == ["invoke"]


def test_protocol_specific_endpoint_and_form_terms_round_trip():
    """The generated IDTA template defines per-protocol vocabulary (modv_*,
    uav_*, opcua schemes) but wires none of it into the generic
    EndpointMetadata/forms — the DMP extension subclasses do, so a
    hand-authored protocol AID parses COMPLETELY (OPC-10101 §6.3.3/§6.5.3,
    WoT Modbus binding)."""
    from aas_model.submodel_templates.aid import (
        DmpModbusInterface, DmpOpcuaInterface, ModbusForm, OpcuaForm,
        OpcuaSecurityDefinitions,
    )
    from aas_model.testing import modbus_interface, opcua_interface
    from aas_pydantic import Property

    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription")
    modbus = modbus_interface(
        "modbus://192.168.0.70:502",
        properties={"Coil1": "/Coil,1"},
        actions={"WriteCoil": ("/Coil,1", "POST")})
    modbus.EndpointMetadata.modv_mostSignificantByte = Property(
        semantic_id="https://www.w3.org/2019/wot/modbus#hasMostSignificantByte",
        value="false")
    modbus.InteractionMetadata.actions.property_name["WriteCoil"].forms.modv_function = Property(
        semantic_id="https://www.w3.org/2019/wot/modbus#hasFunction",
        value="writeSingleCoil")
    aid.InterfaceTemplateForMODBUS["interface_modbus"] = modbus

    opcua = opcua_interface(
        "opc.tcp://192.168.0.90:4840",
        actions={"Calibrate": ("/?id=ns=2;s=RunCalibration", "POST",
                               "ns=1;s=CalibrationObject")})
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        Scheme, UavSecurityMode, UavSecurityPolicy, opcua_channel_sc,
    )
    # named-field convention: field name == id_short — stamp it (post-
    # validation mutation bypasses the model's automatic stamping)
    channel = opcua_channel_sc(
        scheme=Scheme(value="opcua_channel_sc"),
        uav_securityMode=UavSecurityMode(value="SignAndEncrypt"),
        uav_securityPolicy=UavSecurityPolicy(value="Basic256Sha256"))
    channel.id_short = "opcua_channel_sc"
    opcua.EndpointMetadata.securityDefinitions.opcua_channel_sc = channel
    aid.InterfaceTemplateForOPCUA["interface_opcua"] = opcua

    # serialize → parse back: the protocol terms survive (they previously
    # could not even be authored — extra_forbidden on the generic classes)
    doc = _roundtrip(aid)
    back = parse_submodel_dict(doc, DmpAssetInterfacesDescription)

    mb = back.InterfaceTemplateForMODBUS["interface_modbus"]
    assert isinstance(mb, DmpModbusInterface)
    assert mb.EndpointMetadata.modv_mostSignificantByte.value == "false"
    action = mb.InteractionMetadata.actions.property_name["WriteCoil"]
    assert isinstance(action.forms, ModbusForm)
    assert action.forms.modv_function.value == "writeSingleCoil"

    oc = back.InterfaceTemplateForOPCUA["interface_opcua"]
    assert isinstance(oc, DmpOpcuaInterface)
    security = oc.EndpointMetadata.securityDefinitions
    assert isinstance(security, OpcuaSecurityDefinitions)
    assert security.opcua_channel_sc.uav_securityMode.value == "SignAndEncrypt"
    assert security.opcua_channel_sc.uav_securityPolicy.value == "Basic256Sha256"


def _roundtrip(aid_model) -> dict:
    import json

    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    from basyx.aas.adapter.json import json_serialization

    from aas_model.constants import BASE_URL
    from aas_model.resource_template import ResourceTypeAAS
    asset = ResourceTypeAAS(
        id_short="RoundTrip",
        id=f"{BASE_URL}/aas/RoundTrip",
        asset_type="RoundTrip",
    )
    asset.asset_interfaces_description = aid_model
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    return next(s for s in doc["submodels"]
                if s.get("idShort") == aid_model.id_short)

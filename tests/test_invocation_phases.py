"""Operation-mapping phases (DMP PLAN P3): command, optional status, response.
MQTT event affordances in the AID extension and the AIMC ``Status*`` and
``Response*`` additions, serialized to AAS JSON as the DMP projects them."""

from __future__ import annotations

import json

from aas_pydantic.convert_pydantic_model import convert_model_to_aas
from aas_pydantic.convert_util import strip_temp_id_short_attributes
from basyx.aas.adapter.json import json_serialization

from aas_model._serde import parse_submodel_dict
from aas_model.constants import (
    AID_EVENT_DATA, AIMC_STATUS_TIMEOUT, AIMC_STATUS_TRANSFORMATION, BASE_URL,
)
from aas_model.resource_template import ResourceTypeAAS
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    mapping_configuration, response_sink, response_source, sink, source, status_source,
)
from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.testing import aimc_ref, mqtt_interface


def _submodels(**submodels) -> dict:
    asset = ResourceTypeAAS(id_short="TwoPhase", id=f"{BASE_URL}/aas/TwoPhase",
                            asset_type="TwoPhase", **submodels)
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    return {submodel["idShort"]: submodel for submodel in doc["submodels"]}


def _child(element: dict, id_short: str) -> dict:
    children = element.get("submodelElements", element.get("value", []))
    return next(child for child in children if child.get("idShort") == id_short)


def _semantic(element: dict) -> str:
    return element["semanticId"]["keys"][0]["value"]


def test_mqtt_event_affordance_serializes_as_a_wot_event_with_its_data_schema():
    interface = mqtt_interface("mqtt://broker:1883/base", properties={"State": "/state"}, events={
        "Finished": ("/events/finished", {"type": "object", "properties": {"code": {"type": "integer"}}})})
    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription",
                                        InterfaceTemplateForMQTT={"interface_mqtt": interface})

    serialized = _submodels(asset_interfaces_description=aid)["AssetInterfacesDescription"]
    interaction = _child(_child(serialized, "interface_mqtt"), "InteractionMetadata")
    events = _child(interaction, "events")
    finished = _child(events, "Finished")
    assert _semantic(events) == "https://www.w3.org/2019/wot/td#EventAffordance"
    assert _semantic(finished) == "https://www.w3.org/2019/wot/td#EventAffordance"
    assert _semantic(_child(finished, "data")) == AID_EVENT_DATA
    assert _child(_child(finished, "data"), "type")["value"] == "object"
    assert _child(_child(finished, "forms"), "op")["value"] == "subscribeevent"

    back = parse_submodel_dict(serialized, DmpAssetInterfacesDescription)
    parsed = back.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.events
    assert list(parsed.property_name) == ["Finished"]


def test_interfaces_without_events_serialize_no_events_container():
    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription", InterfaceTemplateForMQTT={
        "interface_mqtt": mqtt_interface("mqtt://broker:1883/base", properties={"State": "/state"})})
    serialized = _submodels(asset_interfaces_description=aid)["AssetInterfacesDescription"]
    interaction = _child(_child(serialized, "interface_mqtt"), "InteractionMetadata")
    assert "events" not in {child["idShort"] for child in interaction["value"]}


STATUS_LUA = """
function aimc_main(sources, invocation)
  if sources.Done == invocation.baseline.Done then return "running" end
  return "done"
end
"""
RESPONSE_LUA = """
function aimc_main(sources, invocation)
  return { Start = { Result = sources.Result }, Reset = false }
end
"""
AID = "{aas_id}/submodels/AssetInterfacesDescription"
# DMP additions to the IDTA MappingConfiguration: none may claim an IDTA semantic id.
EXTENSION_FIELDS = {"StatusSources", "StatusTransformation", "StatusTimeout", "ResponseSources",
                    "ResponseTransformation", "ResponseSinks", "ExecutionSemantics"}


def _modbus(*path: str):
    return aimc_ref(AID, "interface_modbus", "InteractionMetadata", *path)


def _start_mapping():
    """Modbus: write Speed, set the start coil, poll Done or wait for Finished,
    read Result once, reset the start coil."""
    return mapping_configuration(
        id_short="Start",
        sources=[source("Start", aimc_ref("{aas_id}/submodels/ControlComponentInstance",
                                          "Skills", "Start", "operation"))],
        sinks=[sink("Speed", _modbus("properties", "Speed")), sink("Start", _modbus("actions", "Start"))],
        transformation="function aimc_main(sources) return { Speed = sources.Start.Speed, Start = true } end",
        status_sources=[
            status_source("Done", _modbus("properties", "Done"), polling_interval=0.2),
            status_source("Finished", aimc_ref(AID, "interface_mqtt", "InteractionMetadata", "events", "Finished")),
        ],
        status_transformation=STATUS_LUA,
        status_timeout=30,
        response_sources=[response_source("Result", _modbus("properties", "Result"))],
        response_transformation=RESPONSE_LUA,
        response_sinks=[response_sink("Reset", _modbus("properties", "StartCoil"))],
    )


def _serialized_aimc() -> dict:
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(value=[_start_mapping()]))
    return _submodels(asset_interfaces_mapping_configuration=aimc)["AIMC"]


def _serialized_mapping() -> dict:
    return _child(_serialized_aimc(), "MappingConfigurations")["value"][0]


def test_operation_mapping_serializes_command_status_and_response_phases():
    entry = _serialized_mapping()
    assert [_child(item, "SinkId")["value"] for item in _child(entry, "Sinks")["value"]] == ["Speed", "Start"]
    timeout = _child(entry, "StatusTimeout")
    assert _semantic(timeout) == AIMC_STATUS_TIMEOUT
    assert (timeout["valueType"], timeout["value"]) == ("xs:double", "30.0")
    assert _semantic(_child(entry, "StatusTransformation")) == AIMC_STATUS_TRANSFORMATION
    done, finished = _child(entry, "StatusSources")["value"]
    assert _child(done, "PollingInterval")["value"] == "0.2"
    assert "PollingInterval" not in {child["idShort"] for child in finished["value"]}
    assert _child(finished, "Source")["value"]["keys"][-1]["value"] == "Finished"
    assert "PollingInterval" not in {child["idShort"] for child in _child(entry, "ResponseSources")["value"][0]["value"]}

    back = parse_submodel_dict(_serialized_aimc(), Aimc).MappingConfigurations.value[0]
    assert float(back.StatusTimeout.value) == 30
    assert [item.SourceId.value for item in back.StatusSources.value] == ["Done", "Finished"]
    assert float(back.StatusSources.value[0].PollingInterval.value) == 0.2
    assert back.ResponseSinks.value[0].SinkId.value == "Reset"


def test_every_dmp_addition_uses_the_project_namespace():
    entry = _serialized_mapping()

    def walk(element: dict, inside_extension: bool):
        extension = inside_extension or element.get("idShort") in EXTENSION_FIELDS
        if extension and "semanticId" in element:
            assert _semantic(element).startswith(f"{BASE_URL}/aimc/") or element.get("idShort") == "PollingInterval", \
                f"{element.get('idShort')} has the non-project semantic id {_semantic(element)}"
        for child in element.get("value", []) if isinstance(element.get("value"), list) else []:
            walk(child, extension)

    seen = {child["idShort"] for child in entry["value"]}
    assert EXTENSION_FIELDS - {"ExecutionSemantics"} <= seen
    walk(entry, False)

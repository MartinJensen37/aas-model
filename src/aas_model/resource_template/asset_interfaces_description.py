"""Asset Interfaces Description partial — mandatory Resource actions/properties.

Built on the DMP-extended AID (``aas_model.submodel_templates.aid``), which
inherits from the generated IDTA AssetInterfacesDescription.  Every Resource
must expose the Halt / Occupy / Release actions and a StationState property.

Named-field style: children are DIRECT named fields (no ``value`` wrapper);
dynamic action/property maps are ``Dict[str, X]`` fields on the ``actions`` /
``properties`` containers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..constants import (
    BROKER, SITE, SCHEMA_BASE, AID_SYNCHRONOUS,
    AID_MQTT_REQUEST_REPLY, AID_MQTT_RESPONSE_TOPIC,
)
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, populate_datapoint
from aas_pydantic import Property
from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, DmpActionInput, DmpActionOutput,
    MqttAction, MqttProperty, MqttResponseForm,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Key as AIDKey,
    Title as AIDTitle,
)
from ._helpers import put

# The StationState payload is described by ``stationState.schema.json`` — embed
# its object-schema structure (State enum, ProcessQueue array, TimeStamp) into
# the AID so the interface describes the message instead of only pointing at
# the schema URL.  The schema URL rides as a supplemental semantic id on the
# DataSchema it represents (the property itself for a property; the
# ``input``/``output`` DataSchemas for an action).
_STATION_STATE_SCHEMA = load_schema(f"{SCHEMA_BASE}/stationState.schema.json")

# Action command/response payloads — embedded as the WoT ``input``/``output``
# DataSchemas of every MQTT action (Halt / Occupy / Release / Stoppering).
_COMMAND_SCHEMA = load_schema(f"{SCHEMA_BASE}/command.schema.json")
_COMMAND_RESPONSE_SCHEMA = load_schema(f"{SCHEMA_BASE}/commandResponse.schema.json")

# Published schema URLs carried as supplemental semantic ids on the DataSchemas.
COMMAND_SCHEMA_URL = f"{SCHEMA_BASE}/command.schema.json"
COMMAND_RESPONSE_SCHEMA_URL = f"{SCHEMA_BASE}/commandResponse.schema.json"
STATION_STATE_SCHEMA_URL = f"{SCHEMA_BASE}/stationState.schema.json"


def mqtt_action(
    name: str,
    *,
    synchronous: bool = False,
    has_response: bool = True,
    input_schema: Optional[Dict[str, Any]] = _COMMAND_SCHEMA,
    output_schema: Optional[Dict[str, Any]] = _COMMAND_RESPONSE_SCHEMA,
    input_schema_url: str = COMMAND_SCHEMA_URL,
    output_schema_url: str = COMMAND_RESPONSE_SCHEMA_URL,
) -> MqttAction:
    """Build a standard MQTT action with default form settings.

    ``input_schema`` / ``output_schema`` (already-dereferenced JSON Schema
    dicts) embed the action's WoT ``input`` / ``output`` DataSchemas — by
    default the standard command / commandResponse schemas, so every MQTT
    action carries them (Halt, with ``has_response=False``, has no output).
    Pass ``None`` to omit one.  Each schema URL rides as a supplemental
    semantic id on the DataSchema it represents (``input`` / ``output``),
    not as a separate URL Property.
    """
    action = MqttAction()
    action.title = AIDTitle(id_short="title", value=name)
    action.synchronous = Property(
        id_short="synchronous", semantic_id=AID_SYNCHRONOUS,
        value=str(synchronous).lower())
    if input_schema is not None:
        action.input = datapoint_from_schema(
            input_schema, cls=DmpActionInput, schema_url=input_schema_url
        )
        action.input.id_short = "input"
    if has_response and output_schema is not None:
        action.output = datapoint_from_schema(
            output_schema, cls=DmpActionOutput, schema_url=output_schema_url
        )
        action.output.id_short = "output"
    forms = action.forms
    forms.href.value = f"/CMD/{name}"
    forms.op.value = "invokeaction"
    forms.mqv_retain.value = "false"
    forms.mqv_control_packet.value = "subscribe"
    forms.mqv_qos.value = "2"
    if has_response:
        # MQTT 5 request/reply correlation (WoT MQTT binding): the action is
        # a correlated request/reply exchange; the reply is delivered on the
        # declared response topic (the requester publishes the command with
        # the response-topic + correlation-data properties).
        forms.mqv_request_reply = Property(
            id_short="mqv_request_reply", semantic_id=AID_MQTT_REQUEST_REPLY, value="true")
        forms.mqv_response_topic = Property(
            id_short="mqv_response_topic", semantic_id=AID_MQTT_RESPONSE_TOPIC,
            value=f"/DATA/{name}")
        # Build on the class defaults so the children keep their semanticIds
        # (href → hasTarget, content_type → forContentType, …) — constructing
        # bare ``Property(value=...)`` instances would strip them.
        resp = MqttResponseForm()
        resp.id_short = "response"
        resp.href.value = f"/DATA/{name}"
        resp.contentType.value = "application/json"
        resp.mqv_control_packet.value = "publish"
        resp.mqv_retain.value = "false"
        forms.response = resp
    return action


def mqtt_property(
    name: str, href: str, *, retain: bool = True, qos: int = 0,
    schema: Optional[Dict[str, Any]] = None,
    schema_url: str = STATION_STATE_SCHEMA_URL,
) -> MqttProperty:
    """Build a standard MQTT property with default form settings.

    ``schema`` (an already-dereferenced JSON Schema dict, e.g. from
    :func:`~templates.json_schema_aid.load_schema`) embeds the payload's
    object-schema structure (``type``/``properties``/``items``/``enum``/…)
    into the property via ``populate_datapoint``, leaving the forms untouched.
    The schema URL rides as a supplemental semantic id on the property itself.
    """
    prop = MqttProperty()
    prop.key = AIDKey(id_short="key", value=name)
    prop.title = AIDTitle(id_short="title", value=name)
    forms = prop.forms
    forms.href.value = href
    forms.mqv_retain.value = str(retain).lower()
    forms.mqv_control_packet.value = "publish"
    forms.mqv_qos.value = str(qos)
    if schema is not None:
        populate_datapoint(prop, schema, schema_url=schema_url)
    return prop

def asset_interfaces_description() -> DmpAssetInterfacesDescription:
    """Compatibility entry point backed by the operational MQTT template."""
    from .operational import OperationalMqttInterfaces

    return OperationalMqttInterfaces(id_short="AssetInterfacesDescription")

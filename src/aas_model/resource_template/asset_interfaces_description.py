"""AID schema conversion and event authoring over the generated models.

Fixed operational defaults are declared in ``operational.submodels``; no
protocol is a default.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from aas_pydantic import Key, ModelReference

from ..constants import SCHEMA_BASE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, populate_datapoint
from aas_model.submodel_templates.aid import (
    DmpAction, DmpActionInput, DmpActionOutput, DmpEvent, DmpEventData,
    DmpEvents, DmpProperty, MqttAction, MqvResponseTopic,
    OpcuaAction, OpcuaEvent, OpcuaEventData, OpcuaEventField, OpcuaEventFields, OpcuaEvents,
    ReadOnly, Synchronous, UavComponentOf, UavEventField, UavEventType,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    ContentType as AIDContentType,
    Key as AIDKey,
    MqvQos,
    MqvRetain,
    Observable,
    Title as AIDTitle,
)
from ._helpers import put

# The idShorts of an asset's one interface per protocol. No protocol is a
# default: every reference into the AID names its interface.
MQTT_INTERFACE = "interface_mqtt"
OPCUA_INTERFACE = "interface_opcua"

AID_REF = "{aas_id}/submodels/AssetInterfacesDescription"


def affordance_ref(interface: str, kind: str, name: str) -> ModelReference:
    """Reference to the affordance ``name`` of ``interface``; ``kind`` is
    ``properties``, ``actions`` or ``events``. ``{aas_id}`` is resolved by
    the id injector."""
    return ModelReference(key=(
        Key(type_="Submodel", value=AID_REF),
        Key(type_="SubmodelElementCollection", value=interface),
        Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
        Key(type_="SubmodelElementCollection", value=kind),
        Key(type_="SubmodelElementCollection", value=name),
    ))


# Action command/response payloads — embedded as the WoT ``input``/``output``
# DataSchemas of every action (Halt / Occupy / Release / Stoppering / …).
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
    topic: Optional[str] = None,
) -> MqttAction:
    """Build a standard MQTT action with default form settings.

    The action is published on ``CMD/<topic>`` and answered on
    ``DATA/<topic>``; ``topic`` defaults to the action's name, so an action
    keeps its name where the device's topic differs.

    ``input_schema`` / ``output_schema`` (already-dereferenced JSON Schema
    dicts) embed the action's WoT ``input`` / ``output`` DataSchemas — by
    default the standard command / commandResponse schemas, so every MQTT
    action carries them (Halt, with ``has_response=False``, has no output).
    Pass ``None`` to omit one.  Each schema URL rides as a supplemental
    semantic id on the DataSchema it represents (``input`` / ``output``),
    not as a separate URL Property.
    """
    action = _with_schemas(
        MqttAction(id_short=name), synchronous,
        input_schema, input_schema_url,
        output_schema if has_response else None, output_schema_url,
    )
    # op (invokeaction), mqv_controlPacket (publish) and mqv_retain (false)
    # are the WoT MQTT binding defaults for an action and are not authored.
    forms = action.forms
    topic = topic or name
    forms.href.value = f"CMD/{topic}"
    forms.mqv_qos = MqvQos(value="2")
    if has_response:
        # MQTT 5 request/reply: the request carries this topic as its
        # Response Topic, and the result echoes the Correlation Data.
        forms.mqv_responseTopic = MqvResponseTopic(value=f"DATA/{topic}")
    return action


def opcua_action(
    name: str,
    method: str,
    component_of: str,
    *,
    synchronous: bool = True,
    input_schema: Optional[Dict[str, Any]] = _COMMAND_SCHEMA,
    output_schema: Optional[Dict[str, Any]] = _COMMAND_RESPONSE_SCHEMA,
    input_schema_url: Optional[str] = COMMAND_SCHEMA_URL,
    output_schema_url: Optional[str] = COMMAND_RESPONSE_SCHEMA_URL,
) -> OpcuaAction:
    """Build the OPC UA Method ``method`` (a NodeId) of the Object
    ``component_of`` (OPC 10101 §7.1.3).

    The members of ``input_schema``/``output_schema`` are the Method's
    Input/OutputArguments by name, so a station answers a command with the
    same members over OPC UA as over MQTT. A Call returns with the result,
    hence ``synchronous`` by default.
    """
    action = _with_schemas(
        OpcuaAction(id_short=name, uav_componentOf=UavComponentOf(value=component_of)),
        synchronous, input_schema, input_schema_url, output_schema, output_schema_url,
    )
    action.forms.href.value = f"/?id={method}"
    return action


def _with_schemas(action: DmpAction, synchronous: bool,
                  input_schema: Optional[Dict[str, Any]], input_schema_url: Optional[str],
                  output_schema: Optional[Dict[str, Any]], output_schema_url: Optional[str]):
    action.title = AIDTitle(id_short="title", value=action.id_short)
    action.synchronous = Synchronous(value=str(synchronous).lower())
    if input_schema is not None:
        action.input = datapoint_from_schema(
            input_schema, cls=DmpActionInput, schema_url=input_schema_url
        )
        action.input.id_short = "input"
    if output_schema is not None:
        action.output = datapoint_from_schema(
            output_schema, cls=DmpActionOutput, schema_url=output_schema_url
        )
        action.output.id_short = "output"
    return action


def mqtt_property(
    name: str, href: str, *, retain: bool = True, qos: int = 0,
    writable: bool = False,
    schema: Optional[Dict[str, Any]] = None,
    schema_url: str = STATION_STATE_SCHEMA_URL,
) -> DmpProperty:
    """Build an MQTT property the device publishes on ``href``.

    It is ``observable`` (AID recommends it for every MQTT property) and,
    unless ``writable``, ``readOnly``. The control packet is not authored:
    the WoT MQTT binding defaults (subscribe to read and observe, publish to
    write) apply per operation. ``retain`` marks a retained topic, which
    makes the current value readable.

    ``schema`` (an already-dereferenced JSON Schema dict, e.g. from
    :func:`~templates.json_schema_aid.load_schema`) embeds the payload's
    object-schema structure (``type``/``properties``/``items``/``enum``/…)
    into the property via ``populate_datapoint``, leaving the forms untouched.
    The schema URL rides as a supplemental semantic id on the property itself.
    """
    prop = DmpProperty(id_short=name)
    prop.key = AIDKey(id_short="key", value=name)
    prop.title = AIDTitle(id_short="title", value=name)
    prop.observable = Observable(value="true")
    if not writable:
        prop.readOnly = ReadOnly(value="true")
    forms = prop.forms
    forms.href.value = href
    if retain:
        forms.mqv_retain = MqvRetain(value="true")
    forms.mqv_qos = MqvQos(value=str(qos))
    if schema is not None:
        populate_datapoint(prop, schema, schema_url=schema_url)
    return prop


def opcua_property(
    name: str, node: str, *, schema: Dict[str, Any],
    schema_url: Optional[str] = None, writable: bool = False,
) -> DmpProperty:
    """Build an observable OPC UA variable property on the NodeId ``node``.

    ``observable`` makes the DMP subscribe a monitored item rather than poll;
    unless ``writable`` the property is ``readOnly``. ``schema`` describes
    the variable's value (a scalar or array schema for a built-in type).
    """
    prop = DmpProperty(id_short=name)
    prop.key = AIDKey(id_short="key", value=name)
    prop.title = AIDTitle(id_short="title", value=name)
    prop.observable = Observable(value="true")
    if not writable:
        prop.readOnly = ReadOnly(value="true")
    prop.forms.href.value = f"/?id={node}"
    populate_datapoint(prop, schema, schema_url=schema_url)
    return prop


def mqtt_event(
    name: str, href: str, *, qos: int = 1,
    schema: Optional[Dict[str, Any]] = None,
    schema_url: Optional[str] = None,
) -> DmpEvent:
    """Build an MQTT event affordance the device publishes on ``href``.

    ``op`` (subscribeevent, unsubscribeevent) and ``mqv_controlPacket``
    (subscribe) are the WoT defaults and are not authored; an event is not
    retained, since it has no current value. ``schema`` (an
    already-dereferenced JSON Schema dict) embeds the WoT ``data``
    DataSchema of each notification; ``schema_url`` rides as a supplemental
    semantic id on it. Add the result to an interface with :func:`add_event`.
    """
    event = DmpEvent(id_short=name)
    event.title = AIDTitle(id_short="title", value=name)
    if schema is not None:
        event.data = datapoint_from_schema(schema, cls=DmpEventData, schema_url=schema_url)
        event.data.id_short = "data"
    forms = event.forms
    forms.href.value = href
    forms.mqv_qos = MqvQos(value=str(qos))
    return event


def opcua_event(
    name: str, notifier: str, fields: Dict[str, Any], *,
    event_type: Optional[str] = None,
) -> OpcuaEvent:
    """Build an OPC UA event affordance on the event notifier ``notifier``
    (a NodeId, e.g. ``i=2253`` for the Server object).

    ``fields`` maps each notification field to its JSON Schema, or to
    ``(schema, browse_path)`` when the field is not the namespace-0
    BrowseName of the same name (e.g. ``"0:ToState/0:Id"``); each becomes a
    property of the ``data`` schema (the select clauses). ``event_type`` (an
    EventType NodeId, e.g. ``i=2378`` ProgramTransitionEventType) filters
    the subscription to that type and its subtypes. Both terms are DMP
    terms: OPC 10101 defines no event vocabulary.
    """
    schemas = {n: (v[0] if isinstance(v, tuple) else v) for n, v in fields.items()}
    data = datapoint_from_schema({"type": "object", "properties": schemas}, cls=OpcuaEventData)
    data.id_short = "data"
    selected = {}
    for alias, generic in data.properties.property_name.items():
        spec = fields[generic.key.value if generic.key is not None else alias]
        field = OpcuaEventField(**{f: getattr(generic, f) for f in type(generic).model_fields})
        if isinstance(spec, tuple):
            field.uav_eventField = UavEventField(id_short="uav_eventField", value=spec[1])
        selected[alias] = field
    data.properties = OpcuaEventFields(id_short="properties", property_name=selected)
    event = OpcuaEvent(id_short=name)
    event.title = AIDTitle(id_short="title", value=name)
    event.data = data
    if event_type is not None:
        event.uav_eventType = UavEventType(id_short="uav_eventType", value=event_type)
    forms = event.forms
    forms.href.value = f"/?id={notifier}"
    forms.contentType = AIDContentType(id_short="contentType", value="application/octet-stream")
    return event


def add_event(interface: Any, event: DmpEvent) -> None:
    """Add ``event`` to an MQTT or OPC UA interface's ``events``, creating the
    container on first use (an interface without events serializes none)."""
    im = interface.InteractionMetadata
    if im.events is None:
        im.events = (OpcuaEvents if isinstance(event, OpcuaEvent) else DmpEvents)(id_short="events")
    put(im.events.property_name, event.id_short, event)

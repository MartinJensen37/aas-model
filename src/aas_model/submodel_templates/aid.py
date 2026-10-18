"""
DMP-extended AssetInterfacesDescription — extensions over the generated IDTA AID.

The design and the reasons for every term are in ``docs/aid-extension.md``.
In short:

- The generated IDTA template
  (``aas_pydantic.submodel_templates.asset_interfaces_description``) stays
  pristine, and everything AID 1.2 defines is used as it is: the generated
  ``forms`` already carries every protocol's binding terms
  (``htv_methodName``, ``modv_*``, ``mqv_controlPacket``, ``uav_browsePath``,
  ``bacv_*``, …), and the generated ``EndpointMetadata`` and
  ``securityDefinitions`` cover every protocol.
- This module only adds what AID leaves out (Annex D "EXTERNAL", or not
  mentioned): action and event members, the form's ``op`` and ``response``,
  the property's ``readOnly``/``writeOnly``. They carry their W3C IRIs.
- Terms no specification defines carry ids in this project's namespace:
  ``mqv_responseTopic`` (MQTT 5 request/reply) and the OPC UA event terms
  ``uav_eventType``/``uav_eventField``. ``uav_componentOf`` is OPC 10101's.

Absent terms take their WoT TD defaults; in particular a form without ``op``
serves the affordance's default operations (docs/aid-extension.md §3.4).

Named-field style: containers hold their child elements as DIRECT named
fields (field name == id_short) — no ``value``/``submodel_element`` wrapper.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from pydantic import model_validator

from aas_pydantic import (
    SubmodelElementCollection, SubmodelElementList, Property,
)
from aas_pydantic.aas_model import AasIdString

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    forms as _BaseForm,
    property_name as _BaseProperty,
    property_name_json_schema as _BaseDataSchema,
    properties_json_schema as _BaseSchemaProperties,
    actions as _BaseActions,
    events as _BaseEvents,
    properties as _BaseProperties,
    InteractionMetadata as _BaseInteractionMetadata,
    InterfaceTemplateForMQTT as _BaseMqttInterface,
    InterfaceTemplateForHTTP as _BaseHttpInterface,
    InterfaceTemplateForMODBUS as _BaseModbusInterface,
    InterfaceTemplateForOPCUA as _BaseOpcuaInterface,
    InterfaceTemplateForBacnet as _BaseBacnetInterface,
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST as _BaseIolinkInterface,
    InterfaceTemplateForSNMP as _BaseSnmpInterface,
    InterfaceTemplateForCAN as _BaseCanInterface,
    AssetInterfacesDescription as _BaseAID,
    # Required (One) children of the generated classes — provided here so the
    # variants construct: forms need href/security; the interface needs
    # title + endpoint metadata.
    Title, Base, ContentType, EndpointMetadata, Href,
    security_t, securityDefinitions, uriVariables_t,
    EndpointMetadata_t,
)

from aas_model.constants import (
    AID_ACTION_DEFINITION, AID_EVENT_DEFINITION, AID_WOT_NAME,
    AID_ACTION_INPUT, AID_ACTION_OUTPUT,
    AID_WOT_SAFE, AID_WOT_IDEMPOTENT, AID_SYNCHRONOUS,
    AID_EVENT_SUBSCRIPTION, AID_EVENT_DATA, AID_EVENT_DATA_RESPONSE,
    AID_EVENT_CANCELLATION,
    AID_WOT_READ_ONLY, AID_WOT_WRITE_ONLY,
    AID_WOT_OPERATION_TYPE, AID_WOT_RESPONSE_FORM,
    AID_MQTT_RESPONSE_TOPIC,
    AID_OPCUA_COMPONENT_OF, AID_OPCUA_EVENT_TYPE, AID_OPCUA_EVENT_FIELD,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Leaf terms
# ═══════════════════════════════════════════════════════════════════════════════

class Op(SubmodelElementList):
    """``op`` (hctl:hasOperationType): the WoT operations a form serves, one
    string Property per operation (``readproperty``, ``invokeaction``, …).
    Absent, the affordance's default operations apply; present, it narrows
    them."""
    id_short: AasIdString = "op"
    semantic_id: str = AID_WOT_OPERATION_TYPE
    description: str = "The WoT operation types this form serves. Absent: the default operations of the affordance."
    item_type: ClassVar = Property
    value: List[Property] = []


def op(*operations: str) -> Op:
    """An ``op`` list of the given WoT operation types."""
    return Op(value=[Property(value=o) for o in operations])


class ReadOnly(Property):
    id_short: AasIdString = "readOnly"
    semantic_id: str = AID_WOT_READ_ONLY
    description: str = "The property cannot be written. Default false."
    value_type: str = "xs:boolean"


class WriteOnly(Property):
    id_short: AasIdString = "writeOnly"
    semantic_id: str = AID_WOT_WRITE_ONLY
    description: str = "The property cannot be read. Default false."
    value_type: str = "xs:boolean"


class Safe(Property):
    id_short: AasIdString = "safe"
    semantic_id: str = AID_WOT_SAFE
    description: str = "Invoking the action changes no state. Default false."
    value_type: str = "xs:boolean"


class Idempotent(Property):
    id_short: AasIdString = "idempotent"
    semantic_id: str = AID_WOT_IDEMPOTENT
    description: str = "Repeated invocations with the same input have the same result. Default false."
    value_type: str = "xs:boolean"


class Synchronous(Property):
    id_short: AasIdString = "synchronous"
    semantic_id: str = AID_SYNCHRONOUS
    description: str = "The result of the action arrives in the reply to the invocation. Absent: unknown."
    value_type: str = "xs:boolean"


# ═══════════════════════════════════════════════════════════════════════════════
# Forms
# ═══════════════════════════════════════════════════════════════════════════════

class SnmpvPduType(Property):
    """AID 1.2 SNMP binding (Annex E.1): the PDU type of the interaction,
    ``snmpv:GetRequestPDU`` (read, the default of readproperty) or
    ``snmpv:SetRequestPDU`` (write, the default of writeproperty)."""
    id_short: AasIdString = "snmpv_pduType"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP/pduType"
    description: str = "SNMP PDU type of the interaction: snmpv:GetRequestPDU or snmpv:SetRequestPDU."


class SnmpvVersion(Property):
    """AID 1.2 SNMP binding (Annex E.1): ``snmpv:SNMPv1`` or
    ``snmpv:SNMPv2c`` (the default)."""
    id_short: AasIdString = "snmpv_version"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP/version"
    description: str = "SNMP protocol version of the interaction: snmpv:SNMPv1 or snmpv:SNMPv2c (default)."


class DmpForm(_BaseForm):
    """The AID form plus the optional WoT ``op`` and the SNMP binding's form
    terms (AID 1.2 Annex E.1 defines them, the template carries none)."""
    href: Href = Href()
    op: Optional[Op] = None
    snmpv_pduType: Optional[SnmpvPduType] = None
    snmpv_version: Optional[SnmpvVersion] = None


class DmpResponseForm(SubmodelElementCollection):
    """WoT ExpectedResponse (hctl:returns): the content type of an action's
    result when it differs from the form's. The result arrives over the same
    protocol and form."""
    id_short: AasIdString = "response"
    semantic_id: str = AID_WOT_RESPONSE_FORM
    description: str = "Expected response of the action: its content type. Absent: the form's content type."
    contentType: Optional[ContentType] = None


class DmpActionForm(DmpForm):
    """The form of an action: a form plus the optional WoT ``response``."""
    response: Optional[DmpResponseForm] = None


def _validate_protocol_form(form: DmpForm, protocol: str) -> None:
    prefixes = ("htv_", "modv_", "mqv_", "uav_", "bacv_", "iolv_", "canv_", "snmpv_")
    allowed = f"{protocol}_"
    foreign = [
        name for name in type(form).model_fields
        if name.startswith(prefixes) and not name.startswith(allowed)
        and getattr(form, name) is not None
    ]
    if foreign:
        raise ValueError(f"{type(form).__name__} cannot use foreign protocol fields: {', '.join(foreign)}")


# ═══════════════════════════════════════════════════════════════════════════════
# Property affordances
# ═══════════════════════════════════════════════════════════════════════════════

class DmpProperty(_BaseProperty):
    """The AID PropertyDefinition plus ``readOnly``/``writeOnly`` (AID marks
    them EXTERNAL) and the form's ``op``. ``observable`` is AID's own."""
    readOnly: Optional[ReadOnly] = None
    writeOnly: Optional[WriteOnly] = None
    forms: DmpForm = DmpForm()


class DmpProperties(_BaseProperties):
    """Dynamic map of properties (name → DmpProperty)."""
    property_name: Dict[str, DmpProperty] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Action affordances (AID 1.2 defines the ``actions`` container only)
# ═══════════════════════════════════════════════════════════════════════════════

class DmpActionInput(_BaseDataSchema):
    """``input`` (td:hasInputSchema): the AID data schema of the request
    payload, built with :func:`aas_model.json_schema_aid.datapoint_from_schema`."""
    id_short: AasIdString = "input"
    semantic_id: str = AID_ACTION_INPUT
    description: str = "Data schema of the action's input."


class DmpActionOutput(_BaseDataSchema):
    """``output`` (td:hasOutputSchema): the AID data schema of the result."""
    id_short: AasIdString = "output"
    semantic_id: str = AID_ACTION_OUTPUT
    description: str = "Data schema of the action's output."


class DmpAction(SubmodelElementCollection):
    """One WoT ActionAffordance (TD 1.1 §5.3.1.4); its idShort is the action
    name. The member id mirrors AID's ``PropertyDefinition``: the TD class
    names the ``actions`` container, the member has an id of its own."""
    semantic_id: str = AID_ACTION_DEFINITION
    supplemental_semantic_ids: List[str] = [AID_WOT_NAME]
    description: str = "An invokable function of the asset (WoT ActionAffordance)."
    title: Optional[Title] = None
    safe: Optional[Safe] = None
    idempotent: Optional[Idempotent] = None
    synchronous: Optional[Synchronous] = None
    input: Optional[DmpActionInput] = None
    output: Optional[DmpActionOutput] = None
    uriVariables: Optional[uriVariables_t] = None
    forms: DmpActionForm = DmpActionForm()


class DmpActions(_BaseActions):
    """Dynamic map of actions (name → DmpAction)."""
    property_name: Dict[str, DmpAction] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Event affordances (AID 1.2 defines the ``events`` container only)
# ═══════════════════════════════════════════════════════════════════════════════

class DmpEventSubscription(_BaseDataSchema):
    """``subscription`` (td:hasSubscriptionSchema): payload sent when
    subscribing, e.g. a filter or the callback of an HTTP webhook."""
    id_short: AasIdString = "subscription"
    semantic_id: str = AID_EVENT_SUBSCRIPTION
    description: str = "Data schema of the payload sent when subscribing to the event."


class DmpEventData(_BaseDataSchema):
    """``data`` (td:hasNotificationSchema): payload of each notification."""
    id_short: AasIdString = "data"
    semantic_id: str = AID_EVENT_DATA
    description: str = "Data schema of each event notification."


class DmpEventDataResponse(_BaseDataSchema):
    """``dataResponse`` (td:hasNotificationResponseSchema): the consumer's
    answer to a notification, where a notification is a request."""
    id_short: AasIdString = "dataResponse"
    semantic_id: str = AID_EVENT_DATA_RESPONSE
    description: str = "Data schema of the consumer's response to an event notification."


class DmpEventCancellation(_BaseDataSchema):
    """``cancellation`` (td:hasCancellationSchema): payload sent when
    unsubscribing."""
    id_short: AasIdString = "cancellation"
    semantic_id: str = AID_EVENT_CANCELLATION
    description: str = "Data schema of the payload sent when cancelling the event subscription."


class DmpEvent(SubmodelElementCollection):
    """One WoT EventAffordance (TD 1.1 §5.3.1.5); its idShort is the event
    name. An event has no current value: a consumer only sees notifications
    sent while it is subscribed."""
    semantic_id: str = AID_EVENT_DEFINITION
    supplemental_semantic_ids: List[str] = [AID_WOT_NAME]
    description: str = "A notification pushed by the asset (WoT EventAffordance)."
    title: Optional[Title] = None
    subscription: Optional[DmpEventSubscription] = None
    data: Optional[DmpEventData] = None
    dataResponse: Optional[DmpEventDataResponse] = None
    cancellation: Optional[DmpEventCancellation] = None
    uriVariables: Optional[uriVariables_t] = None
    forms: DmpForm = DmpForm()


class DmpEvents(_BaseEvents):
    """Dynamic map of events (name → DmpEvent)."""
    property_name: Dict[str, DmpEvent] = {}


class DmpInteractionMetadata(_BaseInteractionMetadata):
    """Interaction metadata with the extended properties, actions and events.
    Absent containers stay absent, so an interface without actions or events
    serializes as plain AID."""
    properties: Optional[DmpProperties] = None
    actions: Optional[DmpActions] = None
    events: Optional[DmpEvents] = None


# ═══════════════════════════════════════════════════════════════════════════════
# MQTT: request/reply actions
# ═══════════════════════════════════════════════════════════════════════════════

class MqvResponseTopic(Property):
    """MQTT 5 request/reply (no W3C term): the topic the device publishes the
    action's result to. The request carries it as its Response Topic together
    with Correlation Data, which the reply echoes. Present = request/reply."""
    id_short: AasIdString = "mqv_responseTopic"
    semantic_id: str = AID_MQTT_RESPONSE_TOPIC
    description: str = "Topic the action's result is published to (MQTT 5 Response Topic); the reply echoes the request's Correlation Data."


class MqttActionForm(DmpActionForm):
    """The form of an MQTT action: ``href`` is the request topic,
    ``mqv_controlPacket`` defaults to ``publish`` (WoT MQTT binding)."""
    mqv_responseTopic: Optional[MqvResponseTopic] = None

    @model_validator(mode="after")
    def validate_protocol_fields(self):
        _validate_protocol_form(self, "mqv")
        return self


class MqttAction(DmpAction):
    forms: MqttActionForm = MqttActionForm()


class MqttActions(DmpActions):
    """Dynamic map of MQTT actions (name → MqttAction)."""
    property_name: Dict[str, MqttAction] = {}


class MqttInteractionMetadata(DmpInteractionMetadata):
    actions: Optional[MqttActions] = None


# ═══════════════════════════════════════════════════════════════════════════════
# OPC UA: Method actions (OPC 10101) and events (no OPC 10101 vocabulary)
# ═══════════════════════════════════════════════════════════════════════════════

class UavComponentOf(Property):
    """``uav:componentOf`` (OPC 10101 §7.1.3): the NodeId of the Object that
    owns the Method. Mandatory on OPC UA actions; the Call service addresses
    a Method as (objectId, methodId)."""
    id_short: AasIdString = "uav_componentOf"
    semantic_id: str = AID_OPCUA_COMPONENT_OF
    description: str = "NodeId of the UA Object the method is defined in (the objectId of the UA Call service)."


class OpcuaActionForm(DmpActionForm):
    """OPC UA action form; permits OPC UA binding fields, not other protocols."""
    @model_validator(mode="after")
    def validate_protocol_fields(self):
        _validate_protocol_form(self, "uav")
        return self


class OpcuaAction(DmpAction):
    """An OPC UA Method: the form ``href`` is ``/?id=<Method NodeId>``, input
    and output are its arguments."""
    uav_componentOf: Optional[UavComponentOf] = None
    forms: OpcuaActionForm = OpcuaActionForm()

    @model_validator(mode="after")
    def validate_component_of(self):
        value = self.uav_componentOf.value if self.uav_componentOf is not None else None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("OPC UA actions require a non-empty uav_componentOf NodeId")
        return self


class OpcuaActions(DmpActions):
    """Dynamic map of OPC UA actions (name → OpcuaAction)."""
    property_name: Dict[str, OpcuaAction] = {}


class UavEventType(Property):
    """The OPC UA EventType a subscription is filtered to (where clause:
    ``OfType``), e.g. ``i=2378`` (ProgramTransitionEventType) or
    ``nsu=urn:vendor;s=JobDoneEventType``. Events of subtypes pass too;
    without the term every event of the notifier is delivered."""
    id_short: AasIdString = "uav_eventType"
    semantic_id: str = AID_OPCUA_EVENT_TYPE
    description: str = "NodeId of the OPC UA EventType the subscription is filtered to (OfType); subtypes are included."


class UavEventField(Property):
    """Browse path of an event field relative to the event (select clause),
    as ``/``-separated qualified names, e.g. ``0:ToState/0:Id``; a name
    without ``<namespaceIndex>:`` is in namespace 0. Without the term the
    data-schema property's own name is the field's BrowseName in namespace
    0 — so ``Message``, ``Severity``, ``Time``, ``SourceName``, ``EventType``
    need no term."""
    id_short: AasIdString = "uav_eventField"
    semantic_id: str = AID_OPCUA_EVENT_FIELD
    description: str = "Browse path of the event field relative to the event, e.g. 0:ToState/0:Id (select clause)."


class OpcuaEventField(_BaseDataSchema):
    """One property of an OPC UA event's ``data`` schema: one selected
    event field, optionally with its browse path."""
    uav_eventField: Optional[UavEventField] = None


class OpcuaEventFields(_BaseSchemaProperties):
    """The properties of an OPC UA event's ``data`` schema (name → field)."""
    property_name: Dict[str, OpcuaEventField] = {}


class OpcuaEventData(DmpEventData):
    """``data`` of an OPC UA event: an object schema, one property per
    selected event field. A notification is delivered as that object."""
    properties: Optional[OpcuaEventFields] = None


class OpcuaEvent(DmpEvent):
    """An OPC UA event (OPC 10000-3 §5.4, 10000-4 §7.22.3): the form ``href``
    NodeId (or ``uav_browsePath``) names the event notifier (e.g. the
    ``Server`` object ``i=2253``); ``data`` selects the event fields and the
    optional ``uav_eventType`` filters by EventType. Consumed with an event
    monitored item."""
    uav_eventType: Optional[UavEventType] = None
    data: Optional[OpcuaEventData] = None


class OpcuaEvents(DmpEvents):
    """Dynamic map of OPC UA events (name → OpcuaEvent)."""
    property_name: Dict[str, OpcuaEvent] = {}


class OpcuaInteractionMetadata(DmpInteractionMetadata):
    actions: Optional[OpcuaActions] = None
    events: Optional[OpcuaEvents] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Interfaces
# ═══════════════════════════════════════════════════════════════════════════════

def _endpoint_metadata() -> EndpointMetadata:
    return EndpointMetadata(
        base=Base(),
        contentType=ContentType(),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )


class DmpHttpInterface(_BaseHttpInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class DmpModbusInterface(_BaseModbusInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class DmpBacnetInterface(_BaseBacnetInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class DmpIolinkInterface(_BaseIolinkInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class DmpSnmpInterface(_BaseSnmpInterface):
    """AID 1.2 SNMP v1/v2c interface: base ``snmp://{address}:{port}``, forms
    addressing one OID each."""
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class DmpCanInterface(_BaseCanInterface):
    """AID 1.2 CAN interface (Annex E.2): forms address a frame by its 29-bit
    identifier (``can://0x1f2b3a00``) and a datapoint by the generated
    ``canv_*`` terms; ``base`` is unused for CAN.

    The DMP does not consume CAN (it is not IP-based; a gateway at the bus
    does), but an asset's AID describes all its interfaces, and a CAN AID is
    what configures such a gateway. Like every other interface it carries the
    extended interaction metadata (``op``, ``readOnly``/``writeOnly``,
    actions and events) rather than the bare generated template."""
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()


class MqttInterface(_BaseMqttInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: MqttInteractionMetadata = MqttInteractionMetadata()


class DmpOpcuaInterface(_BaseOpcuaInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = _endpoint_metadata()
    InteractionMetadata: OpcuaInteractionMetadata = OpcuaInteractionMetadata()


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level AID submodel
# ═══════════════════════════════════════════════════════════════════════════════

class DmpAssetInterfacesDescription(_BaseAID):
    """DMP-extended Asset Interfaces Description.

    Every interface lives in its protocol family's ``InterfaceTemplateFor*``
    dict, keyed by its idShort (the DMP convention: the asset's one native
    MQTT interface is ``InterfaceTemplateForMQTT["interface_mqtt"]``). The
    interface families share the ``…/Interface`` semanticId; the parser
    tells them apart by their protocol-binding supplemental IRI.
    """
    InterfaceTemplateForHTTP: Dict[str, DmpHttpInterface] = {}
    InterfaceTemplateForMODBUS: Dict[str, DmpModbusInterface] = {}
    InterfaceTemplateForMQTT: Dict[str, MqttInterface] = {
        "interface_mqtt": MqttInterface(),
    }
    InterfaceTemplateForOPCUA: Dict[str, DmpOpcuaInterface] = {}
    InterfaceTemplateForBacnet: Dict[str, DmpBacnetInterface] = {}
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST: Dict[str, DmpIolinkInterface] = {}
    InterfaceTemplateForSNMP: Dict[str, DmpSnmpInterface] = {}
    InterfaceTemplateForCAN: Dict[str, DmpCanInterface] = {}

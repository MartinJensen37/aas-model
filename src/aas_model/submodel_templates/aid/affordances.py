"""Interaction affordances: AID's property affordance with the data schema
terms, and the action and event affordances AID 1.2 only names as containers
(docs/aid-extension.md §3.1–3.3), plus the interaction metadata that holds
them. Protocol-specific affordance terms live in the bindings."""

from __future__ import annotations

from typing import Dict, List, Optional

from aas_pydantic import Property, SubmodelElementCollection
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    InteractionMetadata as _BaseInteractionMetadata,
    Title,
    actions as _BaseActions,
    events as _BaseEvents,
    properties as _BaseProperties,
    property_name as _BaseProperty,
    uriVariables_t,
)

from aas_model.constants import (
    AID_ACTION_DEFINITION, AID_ACTION_INPUT, AID_ACTION_OUTPUT, AID_EVENT_CANCELLATION, AID_EVENT_DATA,
    AID_EVENT_DATA_RESPONSE, AID_EVENT_DEFINITION, AID_EVENT_SUBSCRIPTION, AID_SYNCHRONOUS,
    AID_WOT_IDEMPOTENT, AID_WOT_NAME, AID_WOT_SAFE,
)
from aas_model.submodel_templates.aid.data_schema import (
    DataSchemaTerms, DmpDataSchema, DmpItems, DmpSchemaProperties,
)
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm


# ── Property affordances ─────────────────────────────────────────────────────

class DmpProperty(_BaseProperty, DataSchemaTerms):
    """The AID PropertyDefinition plus the :class:`DataSchemaTerms`
    (``readOnly``/``writeOnly`` say which operations the property serves) and
    the form's ``op``. ``observable`` is AID's own."""
    items: Optional[DmpItems] = None
    properties: Optional[DmpSchemaProperties] = None
    forms: DmpForm = DmpForm()


class DmpProperties(_BaseProperties):
    """Dynamic map of properties (name → DmpProperty)."""
    property_name: Dict[str, DmpProperty] = {}


# ── Action affordances (AID 1.2 defines the ``actions`` container only) ─────

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


class DmpActionInput(DmpDataSchema):
    """``input`` (td:hasInputSchema): the AID data schema of the request
    payload, built with :func:`aas_model.json_schema_aid.datapoint_from_schema`."""
    id_short: AasIdString = "input"
    semantic_id: str = AID_ACTION_INPUT
    description: str = "Data schema of the action's input."


class DmpActionOutput(DmpDataSchema):
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


# ── Event affordances (AID 1.2 defines the ``events`` container only) ───────

class DmpEventSubscription(DmpDataSchema):
    """``subscription`` (td:hasSubscriptionSchema): payload sent when
    subscribing, e.g. a filter or the callback of an HTTP webhook."""
    id_short: AasIdString = "subscription"
    semantic_id: str = AID_EVENT_SUBSCRIPTION
    description: str = "Data schema of the payload sent when subscribing to the event."


class DmpEventData(DmpDataSchema):
    """``data`` (td:hasNotificationSchema): payload of each notification."""
    id_short: AasIdString = "data"
    semantic_id: str = AID_EVENT_DATA
    description: str = "Data schema of each event notification."


class DmpEventDataResponse(DmpDataSchema):
    """``dataResponse`` (td:hasNotificationResponseSchema): the consumer's
    answer to a notification, where a notification is a request."""
    id_short: AasIdString = "dataResponse"
    semantic_id: str = AID_EVENT_DATA_RESPONSE
    description: str = "Data schema of the consumer's response to an event notification."


class DmpEventCancellation(DmpDataSchema):
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


DmpProperty.model_rebuild()

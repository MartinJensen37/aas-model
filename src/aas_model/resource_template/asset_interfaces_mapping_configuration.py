"""AIMC reference paths and schema-preserving mapping construction.

Fixed MQTT/PackML mappings are declared in ``operational.submodels``.
"""

from __future__ import annotations

from aas_pydantic import (
    Key, ModelReference, Property, ReferenceElement,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    SourcesItem as Source, SinksItem as Sink, Sources, Sinks,
    Source as SourceReference, Sink as SinkReference,
    SourceId, SinkId,
    DefaultPollingInterval,
)

from aas_model.submodel_templates import (
    AimcMappingConfiguration,
    DmpResponseSink, DmpResponseSinkReference, DmpResponseSinkId,
    DmpResponseSinks, DmpResponseSource, DmpResponseSourceReference,
    DmpResponseSourceId, DmpResponseSources, DmpExecutionSemantics,
    DmpTriggerSourceIds, DmpResponseTransformation, Transformation,
)

# ── Reference paths (self-referential — {aas_id} resolved by id_injector) ──
AID_REF = "{aas_id}/submodels/AssetInterfacesDescription"
CCI_REF = "{aas_id}/submodels/ControlComponentInstance"
VARIABLES_REF = "{aas_id}/submodels/Variables"

AID_PROPERTY_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_mqtt"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="properties"),
)

AID_MQTT_ACTION_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_mqtt"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="actions"),
)

VARIABLE_PATH = (
    Key(type_="Submodel", value=VARIABLES_REF),
)


def _property_ref(property_name: str) -> ModelReference:
    """Reference to an AID property (source) — e.g. .../properties/StationState."""
    return ModelReference(key=AID_PROPERTY_PATH + (
        Key(type_="SubmodelElementCollection", value=property_name),
    )).model_copy(deep=True)


def _variable_ref(variable_name: str) -> ModelReference:
    """Reference to a Variables submodel element (sink) — e.g. .../Variables/PackMLState.

    A variable is a plain ``Property`` (a group is only used when a variable
    combines several children), so the key type must match what the Variables
    submodel actually stores — the resolver verifies reference key types against
    the repository and rejects a mismatch.
    """
    return ModelReference(key=VARIABLE_PATH + (
        Key(type_="Property", value=variable_name),
    )).model_copy(deep=True)


def _mqtt_action_ref(name: str) -> ModelReference:
    """Reference to a skill's native MQTT command affordance (interface_mqtt)."""
    return ModelReference(key=AID_MQTT_ACTION_PATH + (
        Key(type_="SubmodelElementCollection", value=name),
    )).model_copy(deep=True)


def operation_ref(name: str) -> ModelReference:
    """Reference to a skill's delegated Operation SubmodelElement in the CCI
    (``Skills/<name>/operation``) — the SOURCE of a one-MC operation mapping.
    The trailing key carries the ``Operation`` key type: that is what the
    management node classifies the mapping as an interaction from."""
    return ModelReference(key=(
        Key(type_="Submodel", value=CCI_REF),
        Key(type_="SubmodelElementCollection", value="Skills"),
        Key(type_="SubmodelElementCollection", value=name),
        Key(type_="Operation", value="operation"),
    ))


def source(name: str, ref: ModelReference) -> Source:
    """A single AID source: the affordance reference + a stable source id."""
    return Source(
        id_short=name,
        Source=SourceReference(value=ref),
        SourceId=SourceId(value=name),
    )

def sink(name: str, ref: ModelReference) -> Sink:
    """A single sink: the submodel element reference + a stable sink id."""
    return Sink(
        id_short=name,
        Sink=SinkReference(value=ref),
        SinkId=SinkId(value=name),
    )


def response_source(source_id: str, ref: ModelReference) -> DmpResponseSource:
    """Select a response element under its Lua-visible source id: the
    command's output, a property read once, or a status source's final value."""
    return DmpResponseSource(
        id_short=source_id,
        Source=DmpResponseSourceReference(value=ref),
        SourceId=DmpResponseSourceId(value=source_id),
    )


def response_sink(sink_id: str, ref: ModelReference) -> DmpResponseSink:
    """Route one Lua result value to a correlated response destination."""
    return DmpResponseSink(
        id_short=sink_id,
        Sink=DmpResponseSinkReference(value=ref),
        SinkId=DmpResponseSinkId(value=sink_id),
    )


def mapping_configuration(
    *,
    id_short: str,
    sources: list[Source],
    sinks: list[Sink],
    transformation: str,
    response_sources: list[DmpResponseSource] | None = None,
    response_sinks: list[DmpResponseSink] | None = None,
    trigger_source_ids: list[str] | None = None,
    response_transformation: str | None = None,
) -> AimcMappingConfiguration:
    """One MappingConfiguration: AID sources, AAS sinks and the Lua mapping.
    The response arguments apply to operation mappings."""
    kwargs = dict(
        id_short=id_short,
        DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
        Transformation=Transformation(value=transformation),
        Sources=Sources(value=sources),
        Sinks=Sinks(value=sinks),
    )
    if response_sources is not None:
        kwargs["ResponseSources"] = DmpResponseSources(value=response_sources)
    if response_sinks is not None:
        kwargs["ResponseSinks"] = DmpResponseSinks(value=response_sinks)
    if response_transformation is not None:
        kwargs["ResponseTransformation"] = DmpResponseTransformation(value=response_transformation)
    if trigger_source_ids is not None:
        kwargs["ExecutionSemantics"] = DmpExecutionSemantics(
            TriggerSourceIds=DmpTriggerSourceIds(
                value=[Property(value=source_id) for source_id in trigger_source_ids]))
    return AimcMappingConfiguration(**kwargs)

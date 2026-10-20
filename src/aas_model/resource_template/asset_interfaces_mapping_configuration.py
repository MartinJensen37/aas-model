"""AIMC reference paths and schema-preserving mapping construction.

Fixed PackML mappings (MQTT and OPC UA) are declared in ``operational.submodels``.
"""

from __future__ import annotations

from collections.abc import Sequence

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
# AID affordances are referenced with ``asset_interfaces_description.affordance_ref``.
CCI_REF = "{aas_id}/submodels/ControlComponentInstance"
VARIABLES_REF = "{aas_id}/submodels/Variables"


def variable_ref(variable_name: str) -> ModelReference:
    """Reference to a Variables submodel element (sink) — e.g. .../Variables/PackMLState.

    A variable is a plain ``Property`` (a group is only used when a variable
    combines several children), so the key type must match what the Variables
    submodel actually stores — the resolver verifies reference key types against
    the repository and rejects a mismatch.
    """
    return ModelReference(key=(
        Key(type_="Submodel", value=VARIABLES_REF),
        Key(type_="Property", value=variable_name),
    ))


def operation_ref(name: str) -> ModelReference:
    """Reference to a skill's delegated Operation in the CCI.

    This is the prefix for references to the Operation's concrete variable
    SubmodelElements; AIMC operation Sources and response Sinks must address
    those variables rather than the Operation container itself.
    """
    return ModelReference(key=(
        Key(type_="Submodel", value=CCI_REF),
        Key(type_="SubmodelElementCollection", value="Skills"),
        Key(type_="SubmodelElementCollection", value=name),
        Key(type_="Operation", value="operation"),
    ))


def operation_variable_ref(name: str, variable_name: str, element_type: str = "Property") -> ModelReference:
    """Reference one variable SubmodelElement inside a delegated Operation."""
    return ModelReference(key=(
        *operation_ref(name).key,
        Key(type_=element_type, value=variable_name),
    ))


def source(name: str, ref: ModelReference) -> Source:
    """A single AID source: the affordance reference + a stable source id."""
    return Source(
        id_short=name,
        Source=SourceReference(value=ref),
        SourceId=SourceId(value=name),
    )


def operation_sources(name: str, variable_names: Sequence[str]) -> list[Source]:
    """Expose inputs (including InOut variables) as individual AIMC Sources."""
    return [source(variable, operation_variable_ref(name, variable))
            for variable in variable_names]


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

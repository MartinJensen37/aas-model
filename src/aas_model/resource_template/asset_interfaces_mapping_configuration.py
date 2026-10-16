"""AIMC partial — mandatory Resource live-data mappings (Variables + Operations).

Maps the Resource's mandatory variables AND its skill operations via IDTA
AIMC 2.1 MappingConfigurations:

- **Variables** — ``PackMLState``/``OccupationState`` read from the AID
  ``StationState`` property (``/DATA/State``); the Lua ``transformation``
  picks the JSON field of the payload each variable maps to:

      sources.StationState.State         → PackMLState
      sources.StationState.ProcessQueue  → OccupationState

- **Operations** — each skill's delegated Operation is ONE mapping (DMP v3,
  one-MC authoring): the SOURCE references the skill's Operation
  SubmodelElement in the CCI (``Skills/<name>/operation``), the SINK is the
  skill's NATIVE command affordance in the AID (``interface_mqtt`` action),
    and the ``Transformation`` is the request blob that packs the caller's
    operation invocation into the native command message. The reply blob and
    explicit response endpoint lists are optional; absent endpoint lists retain
    the existing correlated-reply behavior. The management node classifies
    these mappings as interactions from the
  Operation-element source reference and derives the caller-facing REST
  surface by convention (``/operations/{aas_id_short}/{skill}``).

All references use the ``{aas_id}`` / ``{aas_id_short}`` macros (resolved by
id_injector), so the AIMC always points at this AAS's own submodels.

Named-field style: children are DIRECT named fields on the container (no
``value``/``submodel_element`` wrapper).
"""

from __future__ import annotations

from aas_pydantic import (
    Key, ModelReference, Property, ReferenceElement,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    SourcesItem as Source, SinksItem as Sink, Sources, Sinks,
    Source as SourceReference, Sink as SinkReference,
    SourceId, SinkId,
    DefaultPollingInterval, PollingInterval,
)

from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations,
    DmpResponseSink, DmpResponseSinkReference, DmpResponseSinkId,
    DmpResponseSinks, DmpResponseSource, DmpResponseSourceReference,
    DmpResponseSourceId, DmpResponseSources, DmpExecutionSemantics,
    DmpTriggerSourceIds, DmpStatusSource, DmpStatusSourceReference,
    DmpStatusSourceId, DmpStatusSources, DmpStatusTransformation,
    DmpStatusTimeout, DmpResponseTransformation, Transformation,
)
from ._helpers import DEFAULT_SKILLS

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


def status_source(source_id: str, ref: ModelReference, *,
                  polling_interval: float | None = None) -> DmpStatusSource:
    """A status property or event of the action's AID under its Lua-visible
    source id. A ``polling_interval`` (seconds) reads a property at that rate;
    without one, a property or event is subscribed when its form allows."""
    return DmpStatusSource(
        id_short=source_id,
        Source=DmpStatusSourceReference(value=ref),
        PollingInterval=(PollingInterval(value=str(polling_interval))
                         if polling_interval is not None else None),
        SourceId=DmpStatusSourceId(value=source_id),
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
    status_sources: list[DmpStatusSource] | None = None,
    status_transformation: str | None = None,
    status_timeout: float | None = None,
    response_transformation: str | None = None,
) -> AimcMappingConfiguration:
    """One MappingConfiguration: AID sources, AAS sinks and the Lua mapping.
    The status and response arguments apply to operation mappings."""
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
    if status_sources is not None:
        kwargs["StatusSources"] = DmpStatusSources(value=status_sources)
    if status_transformation is not None:
        kwargs["StatusTransformation"] = DmpStatusTransformation(value=status_transformation)
    if status_timeout is not None:
        kwargs["StatusTimeout"] = DmpStatusTimeout(value=str(status_timeout))
    if response_transformation is not None:
        kwargs["ResponseTransformation"] = DmpResponseTransformation(value=response_transformation)
    if trigger_source_ids is not None:
        kwargs["ExecutionSemantics"] = DmpExecutionSemantics(
            TriggerSourceIds=DmpTriggerSourceIds(
                value=[Property(value=source_id) for source_id in trigger_source_ids]))
    return AimcMappingConfiguration(**kwargs)


_DEFAULT_TRANSFORMATION = """\
function aimc_main(sources)
    return {
        PackMLState     = sources.StationState.State,
        OccupationState = sources.StationState.ProcessQueue,
    }
end
"""


def _operation_request_transformation(name: str) -> str:
    """Lua request blob for the skill's ONE operation mapping: the DMP
    receives the caller's operation invocation (the REST body keyed by the
    action) and packs the correlation Uuid into the native command message
    sent to /CMD/<name>."""
    return f"""\
-- Skill '{name}' operation delegation (one-MC): the DMP receives the caller's
-- operation invocation and packs it into the native command message sent to
-- /CMD/{name}, keeping the correlation Uuid (replies pass through unchanged):
function aimc_main(sources)
    local op = sources.{name}
    return {{
        {name} = {{
            Uuid = op.Uuid,
        }},
    }}
end
"""


def variables_mapping_configuration() -> AimcMappingConfiguration:
    """The mandatory Variables mapping: StationState property → PackMLState /
    OccupationState."""
    return mapping_configuration(
        id_short="MQTT",
        sources=[
            source("StationState", _property_ref("StationState")),
        ],
        sinks=[
            sink("PackMLState", _variable_ref("PackMLState")),
            sink("OccupationState", _variable_ref("OccupationState")),
        ],
        transformation=_DEFAULT_TRANSFORMATION,
    )


def skill_operation_mapping_configuration(name: str) -> AimcMappingConfiguration:
    """One skill's operation-delegation MappingConfiguration (DMP v3, one-MC).

    SOURCE = the skill's Operation SubmodelElement in the CCI (``Skills/<name>/
    operation``); SINK = the skill's native MQTT command affordance; the
    Transformation is the REQUEST blob. The management node classifies this
    mapping as an interaction from the Operation-element source reference and
    derives the caller-facing REST surface (``/operations/{aas_id_short}/
    <name>``) by convention."""
    return mapping_configuration(
        id_short=name,
        sources=[
            source(name, operation_ref(name)),
        ],
        sinks=[
            sink(name, _mqtt_action_ref(name)),
        ],
        transformation=_operation_request_transformation(name),
    )


def asset_interfaces_mapping_configuration() -> Aimc:
    """AIMC submodel with the mandatory Resource mappings.

    The Variables mapping (PackMLState/OccupationState ← StationState) plus,
    per default skill, ONE operation-delegation MappingConfiguration (the
    skill's CCI Operation → its native MQTT command affordance).  Resource
    configs add their own skill / operation mappings to
    ``MappingConfigurations``.
    """
    mcs = [variables_mapping_configuration()]
    for name, _synchronous, _has_response in DEFAULT_SKILLS:
        mcs.append(skill_operation_mapping_configuration(name))
    return Aimc(
        id_short="AssetInterfacesMappingConfiguration",
        MappingConfigurations=AimcMappingConfigurations(value=mcs),
    )

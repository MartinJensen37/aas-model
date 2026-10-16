"""DMP-extended AssetInterfacesMappingConfiguration — extensions over the
generated IDTA AIMC.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration``)
stays PRISTINE — the DMP extension lives HERE. A plain IDTA AIMC (Sources,
Sinks, Transformation, DefaultPollingInterval) remains a valid DMP input for
data mappings; every addition is optional and carries a semantic id in this
project's namespace (``constants.AIMC_*``).

An operation mapping (its Source is an AAS Operation, ADR-022) runs up to
three phases per invocation (DMP PLAN P3):

1. **command** — the IDTA ``Transformation`` turns the caller's variables into
   the device command; the IDTA ``Sinks`` are written in order: parameter
   properties of the action's AID first, the action affordance last;
2. **status** (optional) — ``StatusSources`` are sampled until the
   ``StatusTransformation`` reports ``"done"`` or ``"failed"``, bounded by
   ``StatusTimeout``. Purely synchronous actions (OPC UA Method, MQTT 5
   request/reply, HTTP) have no status phase;
3. **response** — ``ResponseSources`` are taken once, the
   ``ResponseTransformation`` builds the caller's reply (also after a failed
   status, so device error codes can be returned) and ``ResponseSinks`` are
   written. A ResponseSink addressing the device's own AID (e.g. resetting a
   start coil) is a cleanup write, made before the reply.
"""

from __future__ import annotations

from typing import ClassVar, List, Optional

from aas_pydantic import (
    Property, ReferenceElement, SubmodelElementCollection, SubmodelElementList,
)

from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    AssetInterfacesMappingConfiguration as _BaseAimc,
    MappingConfigurationsItem as _BaseMappingConfiguration,
    MappingConfigurations as _BaseMappingConfigurations,
    Blob,
)

from aas_model.constants import (
    AIMC_STATUS_SOURCES,
    AIMC_STATUS_SOURCE,
    AIMC_STATUS_SOURCE_REFERENCE,
    AIMC_STATUS_SOURCE_ID,
    AIMC_STATUS_TRANSFORMATION,
    AIMC_STATUS_TIMEOUT,
    AIMC_RESPONSE_SOURCE_REFERENCE,
    AIMC_RESPONSE_SOURCE_ID,
    AIMC_RESPONSE_SINK_REFERENCE,
    AIMC_RESPONSE_SINK_ID,
    AIMC_RESPONSE_SINK,
    AIMC_RESPONSE_SINKS,
    AIMC_RESPONSE_SOURCE,
    AIMC_RESPONSE_SOURCES,
    AIMC_RESPONSE_TRANSFORMATION,
    AIMC_EXECUTION_SEMANTICS,
    AIMC_TRIGGER_SOURCE_IDS,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    PollingInterval as _PollingInterval,
    SinkId as _SinkId,
    SourceId as _SourceId,
)


class DmpResponseTransformation(Blob):
    """Response phase: ResponseSources → the caller's reply (keyed by the
    caller SinkId) and the ResponseSink values. Called as
    ``aimc_main(sources, invocation)``; ``invocation.status`` is ``"done"`` or
    ``"failed"`` after a status phase."""
    semantic_id: str = AIMC_RESPONSE_TRANSFORMATION
    description: str = "The optional response-direction transformation of an operation mapping: the response sources are transformed into the caller's reply and the response sink values. Must contain an \"aimc_main(sources, invocation)\" entrypoint function in Lua; invocation.status is \"done\" or \"failed\" after a status phase. When absent the device reply passes through unchanged."
    content_type: str = "text/plain"


class DmpResponseSourceReference(ReferenceElement):
    semantic_id: str = AIMC_RESPONSE_SOURCE_REFERENCE
    description: str = "Reference to a SubmodelElement used as a correlated response source."


class DmpResponseSourceId(_SourceId):
    semantic_id: str = AIMC_RESPONSE_SOURCE_ID


class DmpResponseSource(SubmodelElementCollection):
    """A response source, taken once per invocation: the command's output, a
    property of the action's AID (read after the command or status phase), or
    an element that is also a StatusSource (the value that ended the wait)."""
    semantic_id: str = AIMC_RESPONSE_SOURCE
    description: str = "A response source: the command output, an element read once after the command or status phase, or a status source's final value."
    Source: DmpResponseSourceReference
    SourceId: DmpResponseSourceId


class DmpResponseSources(SubmodelElementList):
    semantic_id: str = AIMC_RESPONSE_SOURCES
    description: str = "Response sources selected for the correlated response transformation."
    item_type: ClassVar = DmpResponseSource
    value: List[DmpResponseSource] = []


class DmpResponseSinkReference(ReferenceElement):
    semantic_id: str = AIMC_RESPONSE_SINK_REFERENCE
    description: str = "Reference to a SubmodelElement used as a correlated response sink."


class DmpResponseSinkId(_SinkId):
    semantic_id: str = AIMC_RESPONSE_SINK_ID


class DmpResponseSink(SubmodelElementCollection):
    semantic_id: str = AIMC_RESPONSE_SINK
    description: str = "A correlated response sink reference and its transformation identifier."
    Sink: DmpResponseSinkReference
    SinkId: DmpResponseSinkId


class DmpResponseSinks(SubmodelElementList):
    semantic_id: str = AIMC_RESPONSE_SINKS
    description: str = "Response sinks written from the correlated response transformation."
    item_type: ClassVar = DmpResponseSink
    value: List[DmpResponseSink] = []


class DmpTriggerSourceIds(SubmodelElementList):
    semantic_id: str = AIMC_TRIGGER_SOURCE_IDS
    description: str = "SourceIds whose contributions trigger mapping execution."
    item_type: ClassVar = Property
    type_value_list_element: Optional[str] = "Property"
    value_type_list_element: Optional[str] = "xs:string"
    value: List[Property] = []


class DmpExecutionSemantics(SubmodelElementCollection):
    semantic_id: str = AIMC_EXECUTION_SEMANTICS
    description: str = "Optional execution selection for a MappingConfiguration."
    TriggerSourceIds: DmpTriggerSourceIds


class DmpStatusSourceReference(ReferenceElement):
    semantic_id: str = AIMC_STATUS_SOURCE_REFERENCE
    description: str = "Reference to a property or event affordance of the action's AID that reports the action's progress."


class DmpStatusSourceId(_SourceId):
    semantic_id: str = AIMC_STATUS_SOURCE_ID


class DmpStatusSource(SubmodelElementCollection):
    """A status property (read at ``PollingInterval``, or subscribed when the
    form declares an observation) or a status event of the action's AID."""
    semantic_id: str = AIMC_STATUS_SOURCE
    description: str = "A status source: a property or event of the action's AID, sampled while the triggered action runs."
    Source: DmpStatusSourceReference
    PollingInterval: Optional[_PollingInterval] = None
    SourceId: DmpStatusSourceId


class DmpStatusSources(SubmodelElementList):
    semantic_id: str = AIMC_STATUS_SOURCES
    description: str = "Status sources sampled until the status transformation reports that the action has finished or failed."
    item_type: ClassVar = DmpStatusSource
    value: List[DmpStatusSource] = []


class DmpStatusTransformation(Blob):
    """Status phase: decides after every status sample whether the action is
    still running. Called as ``aimc_main(sources, invocation)`` with
    ``invocation.baseline`` (status values before the trigger),
    ``invocation.elapsed`` (seconds), ``invocation.inputs`` (the caller's
    variables) and ``invocation.reply`` (the command's reply or ack)."""
    semantic_id: str = AIMC_STATUS_TRANSFORMATION
    description: str = "Decides from the status sources whether the triggered action is still running. Must contain an \"aimc_main(sources, invocation)\" entrypoint function in Lua returning \"running\", \"done\" or \"failed\" (or a table { state = ..., reason = ... })."
    content_type: str = "text/plain"


class DmpStatusTimeout(Property):
    """How long the status phase may last, in seconds; required with
    ``StatusSources``."""
    semantic_id: str = AIMC_STATUS_TIMEOUT
    description: str = "Time in seconds the operation mapping waits for the status transformation to report that the triggered action has finished or failed; the call fails with a timeout when it expires."
    value_type: str = "xs:double"


class DmpMappingConfiguration(_BaseMappingConfiguration):
    """IDTA MappingConfiguration + optional correlated response mapping."""
    ResponseTransformation: Optional[DmpResponseTransformation] = None
    ResponseSources: Optional[DmpResponseSources] = None
    ResponseSinks: Optional[DmpResponseSinks] = None
    ExecutionSemantics: Optional[DmpExecutionSemantics] = None
    StatusSources: Optional[DmpStatusSources] = None
    StatusTransformation: Optional[DmpStatusTransformation] = None
    StatusTimeout: Optional[DmpStatusTimeout] = None


class DmpMappingConfigurations(_BaseMappingConfigurations):
    """IDTA MappingConfigurations list over the DMP-extended configuration."""
    item_type: ClassVar = DmpMappingConfiguration
    value: List[DmpMappingConfiguration] = []


class DmpAimc(_BaseAimc):
    """IDTA AssetInterfacesMappingConfiguration over the DMP-extended list."""
    MappingConfigurations: DmpMappingConfigurations = DmpMappingConfigurations()

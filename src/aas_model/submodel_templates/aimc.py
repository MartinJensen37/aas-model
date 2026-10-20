"""DMP-extended AssetInterfacesMappingConfiguration — extensions over the
generated IDTA AIMC.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration``)
stays PRISTINE — the DMP extension lives HERE. A plain IDTA AIMC (Sources,
Sinks, Transformation, DefaultPollingInterval) remains a valid DMP input for
data mappings; every addition is optional and carries a semantic id in this
project's namespace (``constants.AIMC_*``).

An operation mapping (its Sources address its individual AAS Operation
variables, ADR-022) invokes one action affordance whose terminal reply is its
result (OPC UA Method, MQTT 5 request/reply on the correlation data, HTTP):

1. **command** — the IDTA ``Transformation`` turns the caller's variables into
   the command; the IDTA ``Sinks`` address the action;
2. **response** — ``ResponseSources`` select the action's output or members
   of it, the ``ResponseTransformation`` maps them, and ``ResponseSinks``
   route each result to an explicit Operation output or InOut variable; other
   sinks are written best effort. The three are authored together. An Operation
   with output or InOut variables needs them; nothing is matched by name.
   Without them the Operation answers with no outputs (an invoke-only action
   such as Halt).

Multi-step device sequences (set parameters, trigger, poll a status, read a
result, reset) are not modelled here; the higher-level control orchestrates
them through ordinary mappings.
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
    SinkId as _SinkId,
    SourceId as _SourceId,
)


class DmpResponseTransformation(Blob):
    """Response phase: the action's reply, projected by the ResponseSources →
    the ResponseSink values keyed by SinkId; the SinkId of the ResponseSink
    selecting the Operation carries the caller's outputs. Called as
    ``aimc_main(sources)``."""
    semantic_id: str = AIMC_RESPONSE_TRANSFORMATION
    description: str = "The response-direction transformation of an operation mapping: the action's reply, projected by the response sources, is transformed into the response sink values; the response sink selecting the Operation receives the caller's outputs. Must contain an \"aimc_main(sources)\" entrypoint function in Lua. Authored together with the response sources and sinks; without them the Operation answers with no outputs."
    content_type: str = "text/plain"


class DmpResponseSourceReference(ReferenceElement):
    semantic_id: str = AIMC_RESPONSE_SOURCE_REFERENCE
    description: str = "Reference to a SubmodelElement used as a correlated response source."


class DmpResponseSourceId(_SourceId):
    semantic_id: str = AIMC_RESPONSE_SOURCE_ID


class DmpResponseSource(SubmodelElementCollection):
    """A response source: the action's output, or a member of it."""
    semantic_id: str = AIMC_RESPONSE_SOURCE
    description: str = "A response source: the output of the invoked action, or a member of it."
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


class DmpMappingConfiguration(_BaseMappingConfiguration):
    """IDTA MappingConfiguration + optional correlated response mapping."""
    ResponseTransformation: Optional[DmpResponseTransformation] = None
    ResponseSources: Optional[DmpResponseSources] = None
    ResponseSinks: Optional[DmpResponseSinks] = None
    ExecutionSemantics: Optional[DmpExecutionSemantics] = None


class DmpMappingConfigurations(_BaseMappingConfigurations):
    """IDTA MappingConfigurations list over the DMP-extended configuration."""
    item_type: ClassVar = DmpMappingConfiguration
    value: List[DmpMappingConfiguration] = []


class DmpAimc(_BaseAimc):
    """IDTA AssetInterfacesMappingConfiguration over the DMP-extended list."""
    MappingConfigurations: DmpMappingConfigurations = DmpMappingConfigurations()

"""DMP-extended AssetInterfacesMappingConfiguration — extensions over the
generated IDTA AIMC.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration``)
stays PRISTINE — the DMP extension lives HERE:

- **``DmpMappingConfiguration``** adds the OPTIONAL ``ResponseTransformation``
  blob: the correlated-REPLY direction of an operation mapping. A mapping
  whose SOURCE references an Operation SubmodelElement (the ``Operation`` key
  type classifies it as an interaction, ADR-022) carries the REQUEST
  transformation in the IDTA ``Transformation`` blob and, optionally, the
  RESPONSE transformation in ``ResponseTransformation`` — both directions of
  the bi-directional action contract are then authored explicitly. When the
  response blob is absent the reply passes through unchanged (one-MC
  authoring default).

The semantic id mirrors the IDTA ``Transformation`` vocabulary member
(``.../MappingConfiguration/ResponseTransformation``).
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
    """The correlated-REPLY transformation of an operation mapping: device
    response → caller-facing reply (same ``aimc_main(sources)`` Lua contract,
    keyed by the action name)."""
    semantic_id: str = AIMC_RESPONSE_TRANSFORMATION
    description: str = "The optional response-direction transformation of an operation mapping: the correlated reply from the asset's command affordance is transformed before it is returned to the caller. Must contain an \"aimc_main(sources)\" entrypoint function in Lua. When absent the reply passes through unchanged."
    content_type: str = "text/plain"


class DmpResponseSourceReference(ReferenceElement):
    semantic_id: str = f"{AIMC_RESPONSE_SOURCE}/Source"
    description: str = "Reference to a SubmodelElement used as a correlated response source."


class DmpResponseSourceId(_SourceId):
    semantic_id: str = f"{AIMC_RESPONSE_SOURCE}/SourceId"


class DmpResponseSource(SubmodelElementCollection):
    semantic_id: str = AIMC_RESPONSE_SOURCE
    description: str = "A correlated response source reference and its transformation identifier."
    Source: DmpResponseSourceReference
    SourceId: DmpResponseSourceId


class DmpResponseSources(SubmodelElementList):
    semantic_id: str = AIMC_RESPONSE_SOURCES
    description: str = "Response sources selected for the correlated response transformation."
    item_type: ClassVar = DmpResponseSource
    value: List[DmpResponseSource] = []


class DmpResponseSinkReference(ReferenceElement):
    semantic_id: str = f"{AIMC_RESPONSE_SINK}/Sink"
    description: str = "Reference to a SubmodelElement used as a correlated response sink."


class DmpResponseSinkId(_SinkId):
    semantic_id: str = f"{AIMC_RESPONSE_SINK}/SinkId"


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

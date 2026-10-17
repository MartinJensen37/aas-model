"""
Custom aas_pydantic submodel templates — project-specific and IDTA-extended models.

These models follow the same pattern as aas_pydantic generated templates:
- Submodel/SubmodelElementCollection base classes
- Inline semantic_id, description, qualifiers on every class and leaf element
- Typed leaf elements (Property, ReferenceElement, File, etc.) with defaults

Modules:
    aid                — DMP-extended AID (MQTT + generic WoT action layer)
    execution_model    — Skills ExecutionModel (parameters, conditions, effects)
    skills             — Extended CCI Skill with ExecutionModel
    variables          — Variables submodel (custom, not yet IDTA)
    parameters         — Parameters submodel (custom, not yet IDTA)

The AIMC (AssetInterfacesMappingConfiguration) is extended here (DmpAimc):
the DMP mapping extension adds the OPTIONAL ``ResponseTransformation`` blob
(the correlated-reply direction of an operation mapping, ADR-022) and the
DMP-facing names alias onto the extended classes
(``Aimc`` = ``DmpAimc``, ``AimcMappingConfiguration`` = ``DmpMappingConfiguration``).
"""

from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription,
    DmpAction,
    DmpActionInput,
    DmpActionOutput,
    DmpActions,
    DmpEvent,
    DmpEventSubscription,
    DmpEventData,
    DmpEventDataResponse,
    DmpEventCancellation,
    DmpEvents,
    DmpForm,
    DmpResponseForm,
    DmpHttpInterface,
    DmpModbusInterface,
    DmpOpcuaInterface,
    OpcuaForm,
    OpcuaAction,
    OpcuaProperty,
    OpcuaActions,
    OpcuaEvent,
    OpcuaEvents,
    OpcuaEventData,
    OpcuaEventFields,
    OpcuaEventField,
    UavEventType,
    UavEventField,
    OpcuaProperties,
    UavComponentOf,
    OpcuaInteractionMetadata,
    DmpBacnetInterface,
    DmpIolinkInterface,
    MqttAction,
    MqttActions,
    MqttProperty,
    MqttProperties,
    MqttEvent,
    MqttEvents,
    MqttForm,
    MqttActionForm,
    MqttResponseForm,
    MqttInterface,
)
from aas_model.submodel_templates.aimc import (
    DmpAimc,
    DmpMappingConfiguration,
    DmpMappingConfigurations,
    DmpResponseSinkId,
    DmpResponseSinkReference,
    DmpResponseSink,
    DmpResponseSinks,
    DmpResponseSourceId,
    DmpResponseSourceReference,
    DmpResponseSource,
    DmpResponseSources,
    DmpResponseTransformation,
    DmpStatusSource, DmpStatusSourceReference, DmpStatusSourceId, DmpStatusSources,
    DmpStatusTransformation, DmpStatusTimeout,
    DmpExecutionSemantics,
    DmpTriggerSourceIds,
)
from .control_component_instance import (
    ExecutionModel,
    ExecutionModelParameter,
    Fluent,
    Term,
    ExtendedSkill,
    ExtendedSkills,
    SkillOperation,
    OperationVariableProp,
    SkillInterfaceRelationship,
    ResourceEndpoints,
)
from .variables import Variables
from .parameters import Parameters
# The AIMC submodel is the GENERATED IDTA template + the DMP extension
# (ResponseTransformation, ADR-022). Alias the DMP-facing names onto it.
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Transformation,
)

Aimc = DmpAimc
AimcMappingConfiguration = DmpMappingConfiguration
AimcMappingConfigurations = DmpMappingConfigurations

__all__ = [
    # DMP AID (generated template + MQTT and generic WoT extensions)
    "DmpAssetInterfacesDescription",
    "DmpAction",
    "DmpActions",
    "DmpEvent",
    "DmpEventSubscription",
    "DmpEventData",
    "DmpEventDataResponse",
    "DmpEventCancellation",
    "DmpEvents",
    "MqttEvent",
    "MqttEvents",
    "OpcuaEvent",
    "OpcuaEvents",
    "DmpStatusSource",
    "DmpStatusSourceReference",
    "DmpStatusSourceId",
    "DmpStatusSources",
    "DmpStatusTransformation",
    "DmpStatusTimeout",
    "OpcuaEventData",
    "OpcuaEventFields",
    "OpcuaEventField",
    "UavEventType",
    "UavEventField",
    "DmpForm",
    "DmpResponseForm",
    "MqttActionForm",
    "MqttAction",
    "MqttProperty",
    "MqttForm",
    "MqttResponseForm",
    # Execution model
    "ExecutionModel",
    "ExecutionModelParameter",
    "Fluent",
    "Term",
    # Skills
    "ExtendedSkill",
    "ExtendedSkills",
    "SkillOperation",
    "OperationVariableProp",
    "SkillInterfaceRelationship",
    "ResourceEndpoints",
    # REST AID interface
    # Custom submodels
    "Variables",
    "Parameters",
    "Aimc",
    "AimcMappingConfiguration",
    "AimcMappingConfigurations",
    "Transformation",
    "DmpResponseSource",
    "DmpResponseSources",
    "DmpResponseSourceReference",
    "DmpResponseSourceId",
    "DmpResponseSink",
    "DmpResponseSinks",
    "DmpResponseSinkReference",
    "DmpResponseSinkId",
    "DmpResponseTransformation",
    "DmpExecutionSemantics",
    "DmpTriggerSourceIds",
]

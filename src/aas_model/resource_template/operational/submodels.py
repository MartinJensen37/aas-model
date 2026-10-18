"""Typed defaults for the shared MQTT operational-device contract.

These classes contain the lab's actual command contract. They are not
inherited by protocol-neutral Station/SoftwareResource types. Maps and lists
are composed explicitly; Pydantic deep-copies defaults per constructed model.
"""

from aas_pydantic import Qualifier, ReferenceElement
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, Href,
    Title, security_t, securityDefinitions,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    DefaultPollingInterval, Source, SourceId, Sources, SourcesItem,
    Sink, SinkId, Sinks, SinksItem,
)

from aas_model.constants import BROKER, INVOCATION_ORIGIN, SCHEMA_BASE, SITE
from aas_model.json_schema_aid import load_schema
from aas_model.submodel_templates import Aimc, AimcMappingConfiguration, AimcMappingConfigurations, Transformation
from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, MqttActions, MqttInterface,
    MqttInteractionMetadata,
)
try:
    from aas_model.submodel_templates.aid import DmpProperties as OperationalProperties
except ImportError:
    # The committed AID extension still specializes MQTT properties; the
    # in-flight generic AID extension owns the same map as DmpProperties.
    from aas_model.submodel_templates.aid import MqttProperties as OperationalProperties
from aas_model.resource_template.asset_interfaces_description import mqtt_action, mqtt_property
from aas_model.submodel_templates.control_component_instance import (
    EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, ExtendedSkills,
    OperationVariableProp, ResourceEndpoints, SkillInterfaceRelationship, SkillOperation,
)
from aas_model.submodel_templates.variables import VariableEntry, VariableProp, Variables
from aas_model.resource_template.control_component_instance import (
    ResourceControlComponentInstance, native_action_ref, skill_ref,
)
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    _property_ref, _variable_ref, operation_ref,
)


class OperationalVariables(Variables):
    variable: dict[str, VariableEntry] = {
        "PackMLState": VariableProp(
            id_short="PackMLState", value="",
            supplemental_semantic_ids=["https://w3id.org/2026/apex/semantic/state/operational"],
        ),
        "OccupationState": VariableProp(
            id_short="OccupationState", value="",
            supplemental_semantic_ids=["https://w3id.org/2026/apex/semantic/state/occupied"],
        ),
    }


class OperationalControlComponent(ResourceControlComponentInstance):
    Skills: ExtendedSkills = ExtendedSkills(Skill={
        name: ExtendedSkill(
            id_short=name,
            interface_reference=ReferenceElement(
                semantic_id=EXTENDED_SKILL_INTERFACE_REF,
                description="Reference to the corresponding AID action interface for MQTT topic resolution.",
                value=native_action_ref(name),
            ),
            operation=SkillOperation(
                id_short="operation",
                qualifiers=[
                    Qualifier(
                        type_="invocationDelegation", value_type="xs:string", kind="ConceptQualifier",
                        value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}",
                    ),
                    Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier"),
                ],
                in_output_variable=[OperationVariableProp(
                    id_short="Uuid", description="The UUID of the command",
                )],
                output_variable=[OperationVariableProp(
                    id_short="State", description="The state of the command being executed",
                )],
            ),
        ) for name in ("Halt", "Occupy", "Release")
    })
    Endpoints: ResourceEndpoints = ResourceEndpoints(Endpoint={
        name: SkillInterfaceRelationship(
            id_short=name, first=skill_ref(name), second=native_action_ref(name),
        ) for name in ("Halt", "Occupy", "Release")
    })


class MqttInterfaces(DmpAssetInterfacesDescription):
    """An MQTT interface without implied skills or station telemetry."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        "interface_mqtt": MqttInterface(
            id_short="interface_mqtt",
            EndpointMetadata=EndpointMetadata(
                base=Base(value=f"{BROKER}/{SITE}/{{station_name}}/"),
                contentType=ContentType(value="application/json"),
                security=security_t(), securityDefinitions=securityDefinitions(),
            ),
            InteractionMetadata=MqttInteractionMetadata(
                actions=MqttActions(), properties=OperationalProperties(),
            ),
        ),
    }


class OperationalMqttInterfaces(MqttInterfaces):
    """Shared Halt/Occupy/Release and StationState MQTT affordances."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        "interface_mqtt": MqttInterface(
            id_short="interface_mqtt",
            EndpointMetadata=MqttInterfaces(id_short="AssetInterfacesDescription").InterfaceTemplateForMQTT[
                "interface_mqtt"
            ].EndpointMetadata,
            InteractionMetadata=MqttInteractionMetadata(
                actions=MqttActions(property_name={
                    name: mqtt_action(name, synchronous=True) for name in ("Halt", "Occupy", "Release")
                }),
                properties=OperationalProperties(property_name={
                    "StationState": mqtt_property(
                        "StationState", "DATA/State",
                        schema=load_schema(f"{SCHEMA_BASE}/stationState.schema.json"),
                    ),
                }),
            ),
        ),
    }


class OperationalMqttMappings(Aimc):
    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations(value=[
        AimcMappingConfiguration(
            id_short="MQTT", DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=[SourcesItem(
                id_short="StationState", SourceId=SourceId(value="StationState"),
                Source=Source(value=_property_ref("StationState")),
            )]),
            Sinks=Sinks(value=[SinksItem(
                id_short=name, SinkId=SinkId(value=name), Sink=Sink(value=_variable_ref(name)),
            ) for name in ("PackMLState", "OccupationState")]),
            Transformation=Transformation(value="""function aimc_main(sources)
    return {
        PackMLState = sources.StationState.State,
        OccupationState = sources.StationState.ProcessQueue,
    }
end
"""),
        ),
        *[
            AimcMappingConfiguration(
                id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
                Sources=Sources(value=[SourcesItem(
                    id_short=name, SourceId=SourceId(value=name), Source=Source(value=operation_ref(name)),
                )]),
                Sinks=Sinks(value=[SinksItem(
                    id_short=name, SinkId=SinkId(value=name), Sink=Sink(value=native_action_ref(name)),
                )]),
                Transformation=Transformation(value=(
                    f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.{name}.Uuid }} }} end"
                )),
            ) for name in ("Halt", "Occupy", "Release")
        ],
    ])

"""Syntegon stoppering station instance: the PackML contract and its
Stoppering skill, all over MQTT."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, BROKER, INVOCATION_URL_TEMPLATE, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, SerialNumber,
    YearOfConstruction, CountryOfOrigin,
)
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, EntryNode, HierarchicalStructures, IsPartOf, Node,
)
from aas_model.resource_template.operational import (
    action_member_ref,
    OperationalMqttInterfaces, OperationalMqttControlComponent,
    OperationalMqttMappings, operational_variables, command_reply,
)
from aas_model.resource_template.stations import StopperingStation
from aas_pydantic import ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_model.resource_template.asset_interfaces_description import MQTT_INTERFACE, affordance_ref, mqtt_action
from aas_model.submodel_templates.control_component_instance import (
    EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_model.resource_template.control_component_instance import skill_ref
from aas_model.resource_template.asset_interfaces_mapping_configuration import operation_sources
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem, Source, SourceId, Sink, SinkId, Sources, Sinks, DefaultPollingInterval
from aas_model.submodel_templates import AimcMappingConfiguration, Transformation
from aas_pydantic.submodel_templates.capability_description import CapabilityRealizedBy, CapabilityRelations
from aas_model.invocation_authoring import finalize_invocation_addresses


def syntegon_stoppering() -> StopperingStation:
    identity = "syntegonStopperingSystemAAS"
    serial = "SYN-SS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = StopperingStation(
        id_short=identity, id=resource_id, specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Syntegon Technology GmbH"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Stoppering System 2024"}),
            ManufacturerProductType=ManufacturerProductType(value="Pharmaceutical Stoppering Station"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="DE"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneUp"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={parent: Node(id_short=parent, global_asset_id=f"{BASE_URL}/aas/{parent}")},
                IsPartOf={f"PartOf_{parent}": IsPartOf(
                    id_short=f"PartOf_{parent}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{parent}"),)),
                )},
            ),
        ),
        asset_interfaces_description=OperationalMqttInterfaces(id_short="AssetInterfacesDescription"),
        control_component_instance=OperationalMqttControlComponent(id_short="ControlComponentInstance"),
        asset_interfaces_mapping_configuration=OperationalMqttMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=operational_variables(),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT[MQTT_INTERFACE]
    mqtt.title.value = "Syntegon Stoppering System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Stoppering/"
    resource.parameters.parameter["Location"].x.parameter.value = 480.0

    # Stoppering: CMD/Stoppering answered on DATA/Stoppering (command / commandResponse).
    name = "Stoppering"
    mqtt.InteractionMetadata.actions.property_name[name] = mqtt_action(name, synchronous=False)
    cci = resource.control_component_instance
    cci.Skills.Skill[name] = ExtendedSkill(
        id_short=name, interface_reference=ReferenceElement(
            semantic_id=EXTENDED_SKILL_INTERFACE_REF, value=affordance_ref(MQTT_INTERFACE, "actions", name),
        ),
        operation=SkillOperation(
            id_short="operation", qualifiers=[
                Qualifier(type_="invocationDelegation", value=INVOCATION_URL_TEMPLATE, value_type="xs:string", kind="ConceptQualifier"),
                Qualifier(type_="Asynchronous", value="false", value_type="xs:string", kind="ConceptQualifier"),
            ],
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        id_short=name, first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name),
    )
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=operation_sources(name, ["Uuid"])),
            Sinks=Sinks(value=[SinksItem(id_short=name, Sink=Sink(value=action_member_ref(MQTT_INTERFACE, name, "input")), SinkId=SinkId(value=name))]),
            Transformation=Transformation(value=(
                f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end"
            )),
            # The correlated MQTT reply is the whole commandResponse.
            **command_reply(MQTT_INTERFACE, name, outputs=("Uuid", "State", "Outcome")),
        ),
    )
    container = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={f"RealizedBy_{name}": CapabilityRealizedBy(id_short=f"RealizedBy_{name}", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Processing"), Key(type_="SubmodelElementCollection", value=name), Key(type_="Capability", value="Capability"))), second=skill_ref(name))})
    finalize_invocation_addresses(resource)
    return resource

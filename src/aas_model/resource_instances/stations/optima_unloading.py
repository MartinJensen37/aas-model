"""Optima unloading station instance."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, BROKER, SITE
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
    OperationalMqttInterfaces, OperationalMqttControlComponent,
    OperationalMqttMappings, operational_variables, command_reply,
)
from aas_model.resource_template.stations import UnloadingStation
from aas_model.constants import INVOCATION_ORIGIN, SCHEMA_BASE
from aas_model.json_schema_aid import load_schema
from aas_pydantic import ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_model.submodel_templates import AimcMappingConfiguration, Transformation
from aas_model.resource_template.asset_interfaces_description import MQTT_INTERFACE, affordance_ref, mqtt_action
from aas_model.submodel_templates.control_component_instance import EXTENDED_SKILL_INTERFACE_REF
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Sources, Sinks, SourcesItem, SinksItem, Source, SourceId, Sink, SinkId,
    DefaultPollingInterval,
)
from aas_pydantic.submodel_templates.capability_description import CapabilityRelations, CapabilityRealizedBy
from aas_model.invocation_authoring import finalize_invocation_addresses
from aas_model.resource_template.control_component_instance import skill_ref
from aas_model.resource_template.asset_interfaces_mapping_configuration import operation_sources


def optima_unloading() -> UnloadingStation:
    identity = "optimaUnloadingSystemAAS"
    serial = "OPTIMA-ULS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = UnloadingStation(
        id_short=identity, id=resource_id, specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Optima"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Optima Unloading System"}),
            ManufacturerProductType=ManufacturerProductType(value="Optima Unloading System"),
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
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Optima Unloading System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Unloading/"
    resource.parameters.parameter["Location"].y.parameter.value = 240.0
    mqtt_actions = resource.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name
    cci = resource.control_component_instance
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
    for name in ("Unloading", "Scrap"):
        input_url = f"{SCHEMA_BASE}/command.schema.json"
        output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
        mqtt_actions[name] = mqtt_action(
            name, synchronous=True,
            input_schema=load_schema(input_url), input_schema_url=input_url,
            output_schema=load_schema(output_url), output_schema_url=output_url,
        )
        operation = SkillOperation(id_short="operation", qualifiers=[
            Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"),
            Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier"),
        ], in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")], output_variable=[
            Property(id_short="State", description="The state of the command being executed"),
            Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
        ])
        skill = ExtendedSkill(id_short=name, interface_reference=ReferenceElement(
            semantic_id=EXTENDED_SKILL_INTERFACE_REF, value=affordance_ref(MQTT_INTERFACE, "actions", name),
        ), operation=operation)
        cci.Skills.Skill[name] = skill
        cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(id_short=name, first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name))
        mappings.append(AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=operation_sources(name, ["Uuid"])),
            Sinks=Sinks(value=[SinksItem(id_short=name, Sink=Sink(value=affordance_ref(MQTT_INTERFACE, "actions", name)), SinkId=SinkId(value=name))]),
            Transformation=Transformation(value=(
                f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end"
            )),
            **command_reply(MQTT_INTERFACE, name, outputs=("Uuid", "State", "Outcome")),
        ))
        container = resource.capability_description.CapabilitySet["Handling"].CapabilityContainer[name]
        container.CapabilityRelations = CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={f"RealizedBy_{name}": CapabilityRealizedBy(id_short=f"RealizedBy_{name}", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Handling"), Key(type_="SubmodelElementCollection", value=name), Key(type_="Capability", value="Capability"))), second=skill_ref(name))})
    finalize_invocation_addresses(resource)
    return resource

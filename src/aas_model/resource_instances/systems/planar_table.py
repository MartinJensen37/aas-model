"""Planar table instance."""

from aas_model.constants import BASE_URL, BROKER, CSSX, SCHEMA_BASE, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic import ExternalReference
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, EntryNode, HasPart, HierarchicalStructures, Node,
)
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, SerialNumber,
    YearOfConstruction, CountryOfOrigin,
)
from aas_model.resource_template.operational import MqttInterfaces
from aas_model.json_schema_aid import load_schema
from aas_model.resource_template.systems import CompositeResource
from aas_model.resource_template.asset_interfaces_description import MQTT_INTERFACE, affordance_ref, mqtt_action
from aas_model.submodel_templates.control_component_instance import ExtendedSkill, SkillOperation, SkillInterfaceRelationship
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_model.submodel_templates import Transformation
from aas_pydantic import Key, ModelReference, Property, Qualifier
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import Source as SourceReference, Sink as SinkReference, SourcesItem, SinksItem, Sources, Sinks, SourceId, SinkId, DefaultPollingInterval
from aas_model.resource_template.asset_interfaces_mapping_configuration import operation_sources
from aas_model.constants import INVOCATION_ORIGIN
from aas_model.invocation_authoring import finalize_invocation_addresses
from aas_model.resource_template.operational import command_reply


def planar_table() -> CompositeResource:
    identity = "planarTableAAS"
    serial = "PM-S1-2024-001"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "planarTableShuttle1AAS", "planarTableShuttle2AAS", "planarTableShuttle3AAS",
    )
    table = CompositeResource(
        id_short=identity, id=resource_id, asset_type=f"{CSSX}#PlanarTable",
        specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Table"}),
            ManufacturerProductType=ManufacturerProductType(value="Planar Motors Table"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={child: Node(id_short=child, global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
                HasPart={f"HasPart_{child}": HasPart(
                    id_short=f"HasPart_{child}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{child}"),)),
                ) for child in children},
            ),
        ),
        asset_interfaces_description=MqttInterfaces(id_short="AssetInterfacesDescription"),
    )
    mqtt = table.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Planar Motors Table"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/"
    # Halting the entire table is distinct from halting an individual shuttle.
    name = "Halt"
    table.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name[name] = mqtt_action(
        name, synchronous=True,
        input_schema=load_schema(f"{SCHEMA_BASE}/command.schema.json"),
        input_schema_url=f"{SCHEMA_BASE}/command.schema.json",
        output_schema=load_schema(f"{SCHEMA_BASE}/commandResponse.schema.json"),
        output_schema_url=f"{SCHEMA_BASE}/commandResponse.schema.json",
    )
    skill = ExtendedSkill(id_short=name)
    skill.Disabled.value = "false"
    skill.interface_reference.value = ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"), Key(type_="SubmodelElementCollection", value="interface_mqtt"), Key(type_="SubmodelElementCollection", value="InteractionMetadata"), Key(type_="SubmodelElementCollection", value="actions"), Key(type_="SubmodelElementCollection", value=name)))
    skill.operation = SkillOperation(id_short="operation", qualifiers=[Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"), Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier")], in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")], output_variable=[Property(id_short="State", description="The state of the command being executed")])
    table.control_component_instance.Skills.Skill[name] = skill
    table.control_component_instance.Endpoints.Endpoint[name] = SkillInterfaceRelationship(id_short=name, first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentInstance"), Key(type_="SubmodelElementCollection", value="Skills"), Key(type_="SubmodelElementCollection", value=name))), second=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"), Key(type_="SubmodelElementCollection", value="interface_mqtt"), Key(type_="SubmodelElementCollection", value="InteractionMetadata"), Key(type_="SubmodelElementCollection", value="actions"), Key(type_="SubmodelElementCollection", value=name))))
    table.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        DmpMappingConfiguration(id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"), Transformation=Transformation(value=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end"), Sources=Sources(value=operation_sources(name, ["Uuid"])), Sinks=Sinks(value=[SinksItem(id_short=name, Sink=SinkReference(value=affordance_ref(MQTT_INTERFACE, "actions", name)), SinkId=SinkId(value=name))]),
                                **command_reply(MQTT_INTERFACE, name)),
    )
    finalize_invocation_addresses(table)
    return table

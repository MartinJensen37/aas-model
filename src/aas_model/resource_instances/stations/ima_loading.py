"""IMA loading station instance."""

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
    OperationalMqttInterfaces, OperationalControlComponent,
    OperationalMqttMappings, OperationalVariables,
)
from aas_model.resource_template.stations import LoadingStation
from aas_model.constants import INVOCATION_ORIGIN, SCHEMA_BASE
from aas_model.json_schema_aid import load_schema
from aas_pydantic import ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_model.resource_template.asset_interfaces_description import mqtt_action
from aas_model.submodel_templates.control_component_instance import EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OperationVariableProp
from aas_model.resource_template.control_component_instance import native_action_ref, skill_ref
from aas_model.resource_template.asset_interfaces_mapping_configuration import operation_ref, _mqtt_action_ref
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem, Source, SourceId, Sink, SinkId, Sources, Sinks, DefaultPollingInterval
from aas_model.submodel_templates import AimcMappingConfiguration, Transformation
from aas_pydantic.submodel_templates.capability_description import CapabilityRealizedBy, CapabilityRelations
from aas_model.invocation_authoring import finalize_invocation_addresses


def ima_loading() -> LoadingStation:
    identity = "imaLoadingSystemAAS"
    serial = "IMA-LS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = LoadingStation(
        id_short=identity, id=resource_id, specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "IMA"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "IMA Loading System"}),
            ManufacturerProductType=ManufacturerProductType(value="IMA Loading System"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="IT"),
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
        control_component_instance=OperationalControlComponent(id_short="ControlComponentInstance"),
        asset_interfaces_mapping_configuration=OperationalMqttMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=OperationalVariables(id_short="Variables"),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "IMA Loading System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Loading/"
    position = resource.parameters.parameter["Location"]
    position.x.parameter.value = 360.0
    position.y.parameter.value = 840.0
    position.yaw.parameter.value = 270.0
    name = "Loading"
    input_url = f"{SCHEMA_BASE}/command.schema.json"
    output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
    resource.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name[name] = mqtt_action(
        name, synchronous=False,
        input_schema=load_schema(input_url), input_schema_url=input_url,
        output_schema=load_schema(output_url), output_schema_url=output_url,
    )
    cci = resource.control_component_instance
    skill = ExtendedSkill(
        id_short=name, interface_reference=ReferenceElement(
            semantic_id=EXTENDED_SKILL_INTERFACE_REF, value=native_action_ref(name),
        ),
        operation=SkillOperation(
            id_short="operation", qualifiers=[
                Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"),
                Qualifier(type_="Asynchronous", value="false", value_type="xs:string", kind="ConceptQualifier"),
            ],
            in_output_variable=[OperationVariableProp(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                OperationVariableProp(id_short="State", description="The state of the command being executed"),
                OperationVariableProp(id_short="Outcome", value="0", value_type="xs:integer"),
            ],
        ),
    )
    cci.Skills.Skill[name] = skill
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(id_short=name, first=skill_ref(name), second=native_action_ref(name))
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=[SourcesItem(id_short=name, Source=Source(value=operation_ref(name)), SourceId=SourceId(value=name))]),
            Sinks=Sinks(value=[SinksItem(id_short=name, Sink=Sink(value=_mqtt_action_ref(name)), SinkId=SinkId(value=name))]),
            Transformation=Transformation(value=(
                f"function aimc_main(sources) local op = sources.{name} "
                f"return {{ {name} = {{ Uuid = op.Uuid }} }} end"
            )),
        ),
    )
    container = resource.capability_description.CapabilitySet["Handling"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={f"RealizedBy_{name}": CapabilityRealizedBy(id_short=f"RealizedBy_{name}", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Handling"), Key(type_="SubmodelElementCollection", value=name), Key(type_="Capability", value="Capability"))), second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{{aas_id}}/submodels/ControlComponentInstance/Skills/{name}"),)))})
    finalize_invocation_addresses(resource)
    return resource

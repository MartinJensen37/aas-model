"""AAU production planner instance."""

from aas_model.constants import CSSX, SCHEMA_BASE
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, SerialNumber,
    YearOfConstruction, CountryOfOrigin,
)
from aas_model.resource_template.software import MqttSoftwareResource
from aas_model.resource_template.asset_interfaces_description import mqtt_action, mqtt_property
from aas_model.submodel_templates.control_component_instance import ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OperationVariableProp
from aas_model.submodel_templates.variables import VariableProp
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_model.submodel_templates import Transformation
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    _property_ref, _variable_ref, operation_ref, _mqtt_action_ref,
)
from aas_pydantic import Capability, ExternalReference, Key, ModelReference, Property, Qualifier
from aas_pydantic.submodel_templates.asset_interfaces_description import Key as AIDKey, Title as AIDTitle
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import Source as SourceReference, Sink as SinkReference, SourcesItem, SinksItem, Sources, Sinks, SourceId, SinkId, DefaultPollingInterval
from aas_pydantic.submodel_templates.capability_description import CapabilityContainer, CapabilitySet, CapabilityRelations, CapabilityRealizedBy
from aas_model.json_schema_aid import load_schema, datapoint_from_schema
from aas_model.constants import INVOCATION_ORIGIN
from aas_model.invocation_authoring import finalize_invocation_addresses


def production_planner() -> MqttSoftwareResource:
    identity = "productionPlannerAAS"
    serial = "AAU-PP-2024-001"
    resource = MqttSoftwareResource(
        id_short=identity, id=f"{BASE_URL}/aas/{identity}",
        asset_type=f"{CSSX}#ProductionPlanner", specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=f"{BASE_URL}/aas/{identity}"),
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Production Planner"}),
            ManufacturerProductType=ManufacturerProductType(value="AAU Production Planner"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
    )
    input_url = f"{SCHEMA_BASE}/planningCommand.schema.json"
    output_url = f"{SCHEMA_BASE}/planningResponse.schema.json"
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "AAU Production Planner"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/ProductionPlanner/"
    action = mqtt_action("Plan", synchronous=True,
                         input_schema=load_schema(input_url), input_schema_url=input_url,
                         output_schema=load_schema(output_url), output_schema_url=output_url)
    mqtt.InteractionMetadata.actions.property_name["Plan"] = action
    # Unlike the orchestrator's State schema, the planner reports StationState.
    state_url = f"{SCHEMA_BASE}/stationState.schema.json"
    state = mqtt_property("StationState", "DATA/State", schema=load_schema(state_url), schema_url=state_url)
    mqtt.InteractionMetadata.properties.property_name["StationState"] = state
    resource.variables.variable["PackMLState"] = VariableProp(id_short="PackMLState", semantic_id="https://w3id.org/2026/apex/semantic/state/operational")
    plan = ExtendedSkill(id_short="Plan")
    plan.Disabled.value = "false"
    plan.interface_reference.value = ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"), Key(type_="SubmodelElementCollection", value="interface_mqtt"), Key(type_="SubmodelElementCollection", value="InteractionMetadata"), Key(type_="SubmodelElementCollection", value="actions"), Key(type_="SubmodelElementCollection", value="Plan")))
    plan.operation = SkillOperation(id_short="operation", qualifiers=[Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"), Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier")], in_output_variable=[OperationVariableProp(id_short="Uuid", description="The UUID of the command")], output_variable=[OperationVariableProp(id_short="State", description="The state of the command being executed")])
    plan.operation.input_variable = [
        OperationVariableProp(id_short="Assets", value="[]", description="JSON array of resource AAS identifiers."),
        OperationVariableProp(id_short="Order"),
    ]
    plan.operation.output_variable.extend([
        OperationVariableProp(id_short="ProcessAasId"),
        OperationVariableProp(id_short="ProductAasId"),
        OperationVariableProp(id_short="ErrorMessage"),
    ])
    cci = resource.control_component_instance
    cci.Skills.Skill["Plan"] = plan
    cci.Endpoints.Endpoint["Plan"] = SkillInterfaceRelationship(id_short="Plan", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentInstance"), Key(type_="SubmodelElementCollection", value="Skills"), Key(type_="SubmodelElementCollection", value="Plan"))), second=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"), Key(type_="SubmodelElementCollection", value="interface_mqtt"), Key(type_="SubmodelElementCollection", value="InteractionMetadata"), Key(type_="SubmodelElementCollection", value="actions"), Key(type_="SubmodelElementCollection", value="Plan"))))
    mapping = DmpMappingConfiguration(id_short="Plan", DefaultPollingInterval=DefaultPollingInterval(value="0.0"), Transformation=Transformation(value=""), Sources=Sources(value=[SourcesItem(id_short="Plan", Source=SourceReference(value=operation_ref("Plan")), SourceId=SourceId(value="Plan"))]), Sinks=Sinks(value=[SinksItem(id_short="Plan", Sink=SinkReference(value=_mqtt_action_ref("Plan")), SinkId=SinkId(value="Plan"))]))
    # AAS operation Properties are scalar; the native MQTT schema requires an array.
    mapping.Transformation.value = b"""function aimc_main(sources)
    local op = sources.Plan
    return { Plan = { Uuid = op.Uuid, Assets = json.decode(op.Assets), Order = op.Order } }
end
"""
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(mapping)
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(DmpMappingConfiguration(id_short="ObserveStationState", DefaultPollingInterval=DefaultPollingInterval(value="0.0"), Transformation=Transformation(value="function aimc_main(sources) return { PackMLState = sources.StationState.State } end"), Sources=Sources(value=[SourcesItem(id_short="StationState", Source=SourceReference(value=_property_ref("StationState")), SourceId=SourceId(value="StationState"))]), Sinks=Sinks(value=[SinksItem(id_short="PackMLState", Sink=SinkReference(value=_variable_ref("PackMLState")), SinkId=SinkId(value="PackMLState"))])))
    resource.capability_description.CapabilitySet = {"Planning": CapabilitySet(id_short="Planning", CapabilityContainer={"Plan": CapabilityContainer(id_short="Plan", Capability=Capability(id_short="Capability", semantic_id=f"{CSSX}#Plan"), CapabilityRelations=CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={"RealizedBy_Plan": CapabilityRealizedBy(id_short="RealizedBy_Plan", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Planning"), Key(type_="SubmodelElementCollection", value="Plan"), Key(type_="Capability", value="Capability"))), second=ExternalReference(key=(Key(type_="GlobalReference", value="{aas_id}/submodels/ControlComponentInstance/Skills/Plan"),))) }))})}
    finalize_invocation_addresses(resource)
    return resource

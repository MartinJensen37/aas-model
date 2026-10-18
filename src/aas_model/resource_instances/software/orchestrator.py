"""AAU orchestrator instance, including its native HTTP API."""

from aas_pydantic import (
    Capability, ExternalReference, Key, ModelReference, Property, Qualifier,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, Href, HtvMethodName,
    Key as AIDKey, Title as AIDTitle, security_t, securityDefinitions,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Source as SourceReference, Sink as SinkReference, SourcesItem, SinksItem,
    Sources, Sinks, SourceId, SinkId, DefaultPollingInterval,
)
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilitySet, CapabilityRelations, CapabilityRealizedBy,
)

from aas_model.constants import CSSX, SCHEMA_BASE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, populate_datapoint
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, SerialNumber,
    YearOfConstruction, CountryOfOrigin,
)
from aas_model.resource_template.software import MqttSoftwareResource
from aas_model.resource_template.asset_interfaces_description import mqtt_action, mqtt_property
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OperationVariableProp,
)
from aas_model.submodel_templates.variables import VariableProp
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_model.submodel_templates import Transformation
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    _property_ref, _variable_ref, operation_ref, _mqtt_action_ref,
)
from aas_model.invocation_authoring import finalize_invocation_addresses
from aas_model.submodel_templates.aid import (
    DmpAction, DmpActionInput, DmpActionOutput, DmpActions, DmpForm, DmpHttpInterface,
)
try:
    from aas_model.submodel_templates.aid import DmpProperties, DmpProperty, ReadOnly, Synchronous
except ImportError:
    # The committed AID template does not yet include generic property extensions.
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        properties as DmpProperties, property_name as DmpProperty,
    )
    ReadOnly = None
    Synchronous = Property
from aas_model.constants import INVOCATION_ORIGIN


def orchestrator() -> MqttSoftwareResource:
    identity = "orchestratorAAS"
    serial = "AAU-BT-2024-001"
    resource = MqttSoftwareResource(
        id_short=identity, id=f"{BASE_URL}/aas/{identity}",
        asset_type=f"{CSSX}#Orchestrator", specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=f"{BASE_URL}/aas/{identity}"),
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Orchestrator"}),
            ManufacturerProductType=ManufacturerProductType(value="AAU Orchestrator"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
    )
    aid = resource.asset_interfaces_description
    mqtt = aid.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "AAU Orchestrator"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Orchestrator/"
    interaction = aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata
    cci = resource.control_component_instance
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
    for name in ("Start", "Stop", "Suspend", "Unsuspend", "Reset"):
        input_url = f"{SCHEMA_BASE}/orchestrationCommand.schema.json" if name in (
            "Start", "Unsuspend",
        ) else f"{SCHEMA_BASE}/command.schema.json"
        action = mqtt_action(name, synchronous=True, input_schema=load_schema(input_url), input_schema_url=input_url)
        interaction.actions.property_name[name] = action
        skill = ExtendedSkill(id_short=name)
        skill.Disabled.value = "false"
        skill.interface_reference.value = ModelReference(key=(
            Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"),
            Key(type_="SubmodelElementCollection", value="interface_mqtt"),
            Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
            Key(type_="SubmodelElementCollection", value="actions"),
            Key(type_="SubmodelElementCollection", value=name),
        ))
        skill.operation = SkillOperation(id_short="operation", qualifiers=[
            Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"),
            Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier"),
        ], in_output_variable=[OperationVariableProp(id_short="Uuid", description="The UUID of the command")], output_variable=[OperationVariableProp(id_short="State", description="The state of the command being executed")])
        mapping = DmpMappingConfiguration(
            id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Transformation=Transformation(value=f"function aimc_main(sources) local op = sources.{name} return {{ {name} = {{ Uuid = op.Uuid }} }} end"),
            Sources=Sources(value=[SourcesItem(id_short=name, Source=SourceReference(value=operation_ref(name)), SourceId=SourceId(value=name))]),
            Sinks=Sinks(value=[SinksItem(id_short=name, Sink=SinkReference(value=_mqtt_action_ref(name)), SinkId=SinkId(value=name))]),
        )
        if name in ("Start", "Unsuspend"):
            skill.operation.input_variable = [OperationVariableProp(id_short="Process")]
            mapping.Transformation.value = (
                f"function aimc_main(sources) local op = sources.{name} "
                f"return {{ {name} = {{ Uuid = op.Uuid, Process = op.Process }} }} end"
            ).encode("utf-8")
        cci.Skills.Skill[name] = skill
        cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(id_short=name, first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentInstance"), Key(type_="SubmodelElementCollection", value="Skills"), Key(type_="SubmodelElementCollection", value=name))), second=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/AssetInterfacesDescription"), Key(type_="SubmodelElementCollection", value="interface_mqtt"), Key(type_="SubmodelElementCollection", value="InteractionMetadata"), Key(type_="SubmodelElementCollection", value="actions"), Key(type_="SubmodelElementCollection", value=name))))
        mappings.append(mapping)
    resource.capability_description.CapabilitySet = {
        "Coordination": CapabilitySet(id_short="Coordination", CapabilityContainer={
            "Orchestrate": CapabilityContainer(id_short="Orchestrate", Capability=Capability(id_short="Capability", semantic_id=f"{CSSX}#Orchestrate"), CapabilityRelations=CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={
                "RealizedBy_Start": CapabilityRealizedBy(id_short="RealizedBy_Start", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Coordination"), Key(type_="SubmodelElementCollection", value="Orchestrate"), Key(type_="Capability", value="Capability"))), second=ExternalReference(key=(Key(type_="GlobalReference", value="{aas_id}/submodels/ControlComponentInstance/Skills/Start"),))),
            }))
        })
    }

    state_url = f"{SCHEMA_BASE}/state.schema.json"
    resource.variables.variable["PackMLState"] = VariableProp(id_short="PackMLState", semantic_id="https://w3id.org/2026/apex/semantic/state/operational")
    state = mqtt_property("State", "DATA/State", schema=load_schema(state_url), schema_url=state_url)
    interaction.properties.property_name["State"] = state
    # Software doesn't have station ProcessQueue; declare only actual telemetry.
    mappings.append(DmpMappingConfiguration(id_short="ObserveState", DefaultPollingInterval=DefaultPollingInterval(value="0.0"), Transformation=Transformation(value="function aimc_main(sources) return { PackMLState = sources.State.State } end"), Sources=Sources(value=[SourcesItem(id_short="State", Source=SourceReference(value=_property_ref("State")), SourceId=SourceId(value="State"))]), Sinks=Sinks(value=[SinksItem(id_short="PackMLState", Sink=SinkReference(value=_variable_ref("PackMLState")), SinkId=SinkId(value="PackMLState"))])))

    http = DmpHttpInterface(
        id_short="interface_http",
        title=AIDTitle(value="Orchestrator REST API"),
        EndpointMetadata=EndpointMetadata(
            base=Base(value="http://orchestrator:8090"),
            contentType=ContentType(value="application/json"),
            security=security_t(), securityDefinitions=securityDefinitions(),
        ),
    )
    http.InteractionMetadata.actions = DmpActions(id_short="actions")
    http.InteractionMetadata.properties = DmpProperties(id_short="properties")
    for name in ("Start", "Stop", "Reset"):
        action = DmpAction(id_short=name, title=AIDTitle(id_short="title", value=name), synchronous=Synchronous(id_short="synchronous", value="true"))
        input_schema = "orchestrationCommand" if name == "Start" else "command"
        input_url = f"{SCHEMA_BASE}/{input_schema}.schema.json"
        output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
        action.input = datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url)
        action.input.id_short = "input"
        action.output = datapoint_from_schema(load_schema(output_url), cls=DmpActionOutput, schema_url=output_url)
        action.output.id_short = "output"
        action.forms.href.value = f"/operations/{name}"
        action.forms.htv_methodName = HtvMethodName(id_short="htv_methodName", value="POST")
        http.InteractionMetadata.actions.property_name[name] = action
    health = DmpProperty(id_short="Health", **({"readOnly": ReadOnly(value="true")} if ReadOnly else {}), forms=DmpForm(
        href=Href(value="/health"), htv_methodName=HtvMethodName(value="GET"),
    ))
    health.key = AIDKey(id_short="key", value="Health")
    health.title = AIDTitle(id_short="title", value="Health")
    state_url = f"{SCHEMA_BASE}/state.schema.json"
    populate_datapoint(health, load_schema(state_url), schema_url=state_url)
    http.InteractionMetadata.properties.property_name["Health"] = health
    aid.InterfaceTemplateForHTTP["interface_http"] = http
    finalize_invocation_addresses(resource)
    return resource

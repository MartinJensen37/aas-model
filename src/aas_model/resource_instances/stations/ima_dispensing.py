"""IMA dispensing station instance: the PackML contract, a Dispensing skill
with a configurable volume and the scale's live weight, all over OPC UA."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, CSSX, INVOCATION_ORIGIN, SCHEMA_BASE
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
    OPCUA_STATION, OperationalOpcuaInterfaces, OperationalOpcuaControlComponent,
    OperationalOpcuaMappings, operational_variables,
)
from aas_model.resource_template.stations import DispensingStation
from aas_pydantic import ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem, Source, SourceId, Sink, SinkId, Sources, Sinks, DefaultPollingInterval, PollingInterval
from aas_model.resource_template.control_component_instance import skill_ref
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    operation_sources, operation_variable_ref,
    response_sink, response_source, variable_ref, series_segment_ref,
)
from aas_model.resource_template.operational import action_member_ref
from aas_model.resource_template.asset_interfaces_description import (
    OPCUA_INTERFACE, affordance_ref, opcua_action, opcua_property,
)
from aas_model.submodel_templates.control_component_instance import EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable
from aas_model.submodel_templates import (
    AimcMappingConfiguration, DmpResponseSinks, DmpResponseSources, DmpResponseTransformation, Transformation,
)
from aas_pydantic.submodel_templates.capability_description import CapabilityRelations, CapabilityRealizedBy
from aas_model.json_schema_aid import load_schema
from aas_model.submodel_templates.variables import MeasurementsGroup, VariableProp
from aas_model.submodel_templates.time_series import record_field, time_series
from aas_model.invocation_authoring import finalize_invocation_addresses


# The Dispensing Method's InputArguments: the command plus the volume to fill.
DISPENSE_COMMAND = {
    "type": "object",
    "properties": {
        "Uuid": {"type": "string", "description": "The UUID of the command"},
        "Volume": {"type": "number", "minimum": 0, "unit": "ml", "description": "The volume to dispense"},
    },
    "required": ["Uuid", "Volume"],
}


def ima_dispensing() -> DispensingStation:
    identity = "imaDispensingSystemAAS"
    serial = "IMA-DS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = DispensingStation(
        id_short=identity, id=resource_id, specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "IMA"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "IMA Dispensing System"}),
            ManufacturerProductType=ManufacturerProductType(value="IMA Dispensing System"),
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
        asset_interfaces_description=OperationalOpcuaInterfaces(id_short="AssetInterfacesDescription"),
        control_component_instance=OperationalOpcuaControlComponent(id_short="ControlComponentInstance"),
        asset_interfaces_mapping_configuration=OperationalOpcuaMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=operational_variables(),
    )
    opcua = resource.asset_interfaces_description.InterfaceTemplateForOPCUA[OPCUA_INTERFACE]
    opcua.title.value = "IMA Dispensing System"
    opcua.EndpointMetadata.base.value = "opc.tcp://dispensing-station:4840/dispensing/"
    resource.parameters.parameter["Location"].x.parameter.value = 240.0
    interaction = opcua.InteractionMetadata
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value

    # Dispensing: the Method Station.Dispensing(Uuid, Volume) -> commandResponse.
    name = "Dispensing"
    interaction.actions.property_name[name] = opcua_action(
        name, f"{OPCUA_STATION}.{name}", OPCUA_STATION,
        input_schema=DISPENSE_COMMAND, input_schema_url=None,
    )
    cci = resource.control_component_instance
    cci.Skills.Skill[name] = ExtendedSkill(
        id_short=name, interface_reference=ReferenceElement(
            semantic_id=EXTENDED_SKILL_INTERFACE_REF, value=affordance_ref(OPCUA_INTERFACE, "actions", name),
        ),
        operation=SkillOperation(
            id_short="operation", qualifiers=[
                Qualifier(type_="invocationDelegation", value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}", value_type="xs:string", kind="ConceptQualifier"),
                Qualifier(type_="Synchronous", value="true", value_type="xs:string", kind="ConceptQualifier"),
            ],
            input_variable=[Property(id_short="Volume", value="1.0", value_type="xs:double", description="The volume to dispense in ml")],
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        id_short=name, first=skill_ref(name), second=affordance_ref(OPCUA_INTERFACE, "actions", name),
    )
    # The mapping addresses the members of the Method's arguments: each
    # InputArgument is a Sink, each OutputArgument a ResponseSource, and the
    # Operation (its InOut and output variables) is the ResponseSink.
    command = ("Uuid", "Volume")
    reply = ("Uuid", "State", "Outcome")
    mappings.append(AimcMappingConfiguration(
        id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
        Sources=Sources(value=operation_sources(name, list(command))),
        Sinks=Sinks(value=[SinksItem(
            id_short=member, SinkId=SinkId(value=member),
            Sink=Sink(value=action_member_ref(OPCUA_INTERFACE, name, "input", member)),
        ) for member in command]),
        Transformation=Transformation(value=(
            "function aimc_main(sources) "
            "return { Uuid = sources.Uuid, Volume = sources.Volume } end"
        )),
        ResponseSources=DmpResponseSources(value=[
            response_source(member, action_member_ref(OPCUA_INTERFACE, name, "output", member))
            for member in reply]),
        # Outcome is an Optional output (as in the commandResponse): a nil Outcome is left out.
        ResponseTransformation=DmpResponseTransformation(value=(
            "function aimc_main(sources) return { Uuid = sources.Uuid, "
            "State = sources.State, Outcome = sources.Outcome } end"
        )),
        ResponseSinks=DmpResponseSinks(value=[
            response_sink(member, operation_variable_ref(name, member)) for member in reply
        ]),
    ))
    container = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(id_short="CapabilityRelations", CapabilityRealizedBy={f"RealizedBy_{name}": CapabilityRealizedBy(id_short=f"RealizedBy_{name}", first=ModelReference(key=(Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"), Key(type_="SubmodelElementCollection", value="Processing"), Key(type_="SubmodelElementCollection", value=name), Key(type_="Capability", value="Capability"))), second=skill_ref(name))})

    # Weight: the scale's reading, sampled every 100 ms while it changes.
    weight = load_schema(f"{SCHEMA_BASE}/weight.schema.json")["properties"]["Weight"]
    interaction.properties.property_name["Weight"] = opcua_property(
        "Weight", f"{OPCUA_STATION}.Weight", schema={**weight, "unit": "g"},
    )
    resource.variables.variable["Weight"] = VariableProp(id_short="Weight", value_type="xs:double", value="0.0", supplemental_semantic_ids=[f"{CSSX}#Weight"])
    mappings.append(AimcMappingConfiguration(
        id_short="ObserveWeight", DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
        Sources=Sources(value=[SourcesItem(id_short="Weight", Source=Source(value=affordance_ref(OPCUA_INTERFACE, "properties", "Weight")), SourceId=SourceId(value="Weight"), PollingInterval=PollingInterval(value="0.1"))]),
        Sinks=Sinks(value=[SinksItem(id_short="Weight", Sink=Sink(value=variable_ref("Weight")), SinkId=SinkId(value="Weight"))]),
        Transformation=Transformation(value="function aimc_main(sources) return { Weight = sources.Weight } end"),
    ))
    # The weight's history: the same reading, one row per sample into Variables/Measurements/Weight.
    resource.variables.Measurements = MeasurementsGroup(value={"Weight": time_series(
        name="Dispensed weight", measurement="dispensing_weight",
        fields={"Weight": record_field("xs:double", concept=f"{CSSX}#Weight", description="Weight in g")},
    )})
    mappings.append(AimcMappingConfiguration(
        id_short="WeightHistory", DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
        Sources=Sources(value=[SourcesItem(id_short="Weight", Source=Source(value=affordance_ref(OPCUA_INTERFACE, "properties", "Weight")), SourceId=SourceId(value="Weight"), PollingInterval=PollingInterval(value="0.1"))]),
        Sinks=Sinks(value=[SinksItem(id_short="Live", Sink=Sink(value=series_segment_ref("Measurements", "Weight")), SinkId=SinkId(value="Live"))]),
        Transformation=Transformation(value="function aimc_main(sources) return { Live = { Weight = sources.Weight } } end"),
    ))
    finalize_invocation_addresses(resource)
    return resource

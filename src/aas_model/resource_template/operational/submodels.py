"""Typed defaults for the shared operational-device contract.

Every operational device of the lab has a PackML state machine and the
skills Halt, Occupy and Release. The contract is the same over each
protocol; only its native affordances differ:

- MQTT: ``CMD/<Skill>`` requests answered on ``DATA/<Skill>`` (MQTT 5
  request/reply) and the retained ``DATA/State`` (State + ProcessQueue).
- OPC UA: the Methods ``ns=2;s=Station.<Skill>`` of the ``ns=2;s=Station``
  Object and its variables ``Station.State`` and ``Station.ProcessQueue``.

Halt only invokes (``CMD/Halt`` is not answered, ``Station.Halt`` has no
OutputArguments). Occupy and Release answer with the commandResponse; their
mappings name it as ResponseSource and the Operation as ResponseSink.

These classes are not inherited by protocol-neutral Station/SoftwareResource
types; an instance picks the protocol its asset speaks. Maps and lists are
composed explicitly; Pydantic deep-copies defaults per constructed model.
"""

from aas_pydantic import Property
from aas_pydantic import Key, ModelReference, Qualifier, ReferenceElement
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, security_t, securityDefinitions,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    DefaultPollingInterval, Source, SourceId, Sources, SourcesItem,
    Sink, SinkId, Sinks, SinksItem,
)

from aas_model.constants import BROKER, INVOCATION_ORIGIN, SCHEMA_BASE, SITE
from aas_model.json_schema_aid import load_schema
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations, DmpResponseSinks, DmpResponseSources,
    DmpResponseTransformation, Transformation,
)
from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, DmpOpcuaInterface, DmpProperties, MqttActions,
    MqttInterface, MqttInteractionMetadata, OpcuaActions, OpcuaInteractionMetadata,
)
from aas_model.resource_template.asset_interfaces_description import (
    MQTT_INTERFACE, OPCUA_INTERFACE, affordance_ref, mqtt_action, mqtt_property,
    opcua_action, opcua_property,
)
from aas_model.submodel_templates.control_component_instance import (
    EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, ExtendedSkills, ResourceEndpoints, SkillInterfaceRelationship, SkillOperation,
)
from aas_model.submodel_templates.variables import VariableEntry, VariableProp, Variables
from aas_model.resource_template.control_component_instance import (
    ResourceControlComponentInstance, skill_ref,
)
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    operation_ref, response_sink, response_source, variable_ref,
)


PACKML_SKILLS = ("Halt", "Occupy", "Release")

# Halt only invokes: the station takes the command and answers nothing. Its
# Operation has no outputs, its action no output schema (and over MQTT no
# response topic) and its mapping no response.
INVOKE_ONLY_SKILLS = ("Halt",)

# The OPC UA Object owning the PackML Methods and variables.
OPCUA_STATION = "ns=2;s=Station"

_STATION_STATE = load_schema(f"{SCHEMA_BASE}/stationState.schema.json")


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


# ── Control component: the PackML skills, bound to one interface ─────────────

def _packml_skills(interface: str) -> ExtendedSkills:
    return ExtendedSkills(Skill={
        name: ExtendedSkill(
            id_short=name,
            interface_reference=ReferenceElement(
                semantic_id=EXTENDED_SKILL_INTERFACE_REF,
                description="Reference to the AID action that natively implements this skill.",
                value=affordance_ref(interface, "actions", name),
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
                **_packml_variables(name),
            ),
        ) for name in PACKML_SKILLS
    })


def _packml_variables(name: str) -> dict:
    uuid = Property(id_short="Uuid", description="The UUID of the command")
    if name in INVOKE_ONLY_SKILLS:
        return {"input_variable": [uuid]}
    return {
        "in_output_variable": [uuid],
        "output_variable": [Property(
            id_short="State", description="The state of the command being executed",
        )],
    }


def _packml_endpoints(interface: str) -> ResourceEndpoints:
    return ResourceEndpoints(Endpoint={
        name: SkillInterfaceRelationship(
            id_short=name, first=skill_ref(name), second=affordance_ref(interface, "actions", name),
        ) for name in PACKML_SKILLS
    })


class OperationalMqttControlComponent(ResourceControlComponentInstance):
    Skills: ExtendedSkills = _packml_skills(MQTT_INTERFACE)
    Endpoints: ResourceEndpoints = _packml_endpoints(MQTT_INTERFACE)


class OperationalOpcuaControlComponent(ResourceControlComponentInstance):
    Skills: ExtendedSkills = _packml_skills(OPCUA_INTERFACE)
    Endpoints: ResourceEndpoints = _packml_endpoints(OPCUA_INTERFACE)


# ── Asset interfaces ─────────────────────────────────────────────────────────

class MqttInterfaces(DmpAssetInterfacesDescription):
    """An MQTT interface without implied skills or station telemetry."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        MQTT_INTERFACE: MqttInterface(
            id_short=MQTT_INTERFACE,
            EndpointMetadata=EndpointMetadata(
                base=Base(value=f"{BROKER}/{SITE}/{{station_name}}/"),
                contentType=ContentType(value="application/json"),
                security=security_t(), securityDefinitions=securityDefinitions(),
            ),
            InteractionMetadata=MqttInteractionMetadata(
                actions=MqttActions(), properties=DmpProperties(),
            ),
        ),
    }


class OperationalMqttInterfaces(MqttInterfaces):
    """Shared Halt/Occupy/Release and StationState MQTT affordances."""

    InterfaceTemplateForMQTT: dict[str, MqttInterface] = {
        MQTT_INTERFACE: MqttInterface(
            id_short=MQTT_INTERFACE,
            EndpointMetadata=MqttInterfaces(id_short="AssetInterfacesDescription").InterfaceTemplateForMQTT[
                MQTT_INTERFACE
            ].EndpointMetadata,
            InteractionMetadata=MqttInteractionMetadata(
                actions=MqttActions(property_name={
                    name: mqtt_action(name, synchronous=True, has_response=name not in INVOKE_ONLY_SKILLS)
                    for name in PACKML_SKILLS
                }),
                properties=DmpProperties(property_name={
                    "StationState": mqtt_property(
                        "StationState", "DATA/State", schema=_STATION_STATE,
                    ),
                }),
            ),
        ),
    }


class OpcuaInterfaces(DmpAssetInterfacesDescription):
    """An OPC UA interface without implied skills or station telemetry."""

    InterfaceTemplateForOPCUA: dict[str, DmpOpcuaInterface] = {
        OPCUA_INTERFACE: DmpOpcuaInterface(
            id_short=OPCUA_INTERFACE,
            EndpointMetadata=EndpointMetadata(
                base=Base(value="opc.tcp://{station_name}:4840/"),
                # OPC 10101: the binding's default UA serialization
                contentType=ContentType(value="application/octet-stream"),
                security=security_t(), securityDefinitions=securityDefinitions(),
            ),
            InteractionMetadata=OpcuaInteractionMetadata(
                actions=OpcuaActions(), properties=DmpProperties(),
            ),
        ),
    }


class OperationalOpcuaInterfaces(OpcuaInterfaces):
    """Shared Halt/Occupy/Release Methods and the PackML state variables."""

    InterfaceTemplateForOPCUA: dict[str, DmpOpcuaInterface] = {
        OPCUA_INTERFACE: DmpOpcuaInterface(
            id_short=OPCUA_INTERFACE,
            EndpointMetadata=OpcuaInterfaces(id_short="AssetInterfacesDescription").InterfaceTemplateForOPCUA[
                OPCUA_INTERFACE
            ].EndpointMetadata,
            InteractionMetadata=OpcuaInteractionMetadata(
                actions=OpcuaActions(property_name={
                    name: opcua_action(name, f"{OPCUA_STATION}.{name}", OPCUA_STATION,
                                       **({"output_schema": None, "output_schema_url": None}
                                          if name in INVOKE_ONLY_SKILLS else {}))
                    for name in PACKML_SKILLS
                }),
                properties=DmpProperties(property_name={
                    name: opcua_property(
                        name, f"{OPCUA_STATION}.{name}", schema=_STATION_STATE["properties"][name],
                    ) for name in ("State", "ProcessQueue")
                }),
            ),
        ),
    }


# ── Mappings: observe the PackML state, invoke the skills ───────────────────

def action_member_ref(interface: str, action: str, schema: str, *members: str) -> ModelReference:
    """Reference to the ``input`` or ``output`` DataSchema of an action, or
    to one of its object members (``.../output/properties/State``)."""
    keys = affordance_ref(interface, "actions", action).key + (Key(type_="SubmodelElementCollection", value=schema),)
    for member in members:
        keys += (Key(type_="SubmodelElementCollection", value="properties"),
                 Key(type_="SubmodelElementCollection", value=member))
    return ModelReference(key=keys)


def command_reply(interface: str, name: str, outputs: tuple[str, ...] = ("Uuid", "State")) -> dict:
    """The response of a skill answered by its whole commandResponse: the
    ResponseSource ``Reply`` is the action's output (the decoded OPC UA
    OutputArguments or MQTT reply, by member name), the transformation picks
    the Operation's ``outputs`` from it, and the ResponseSink ``Outputs`` is
    the Operation itself, i.e. its InOut and output variables."""
    fields = ", ".join(f"{member} = reply.{member}" for member in outputs)
    return dict(
        ResponseSources=DmpResponseSources(id_short="ResponseSources", value=[
            response_source("Reply", action_member_ref(interface, name, "output"))]),
        ResponseTransformation=DmpResponseTransformation(id_short="ResponseTransformation", value=(
            f"function aimc_main(sources) local reply = sources.Reply "
            f"return {{ Outputs = {{ {fields} }} }} end"
        )),
        ResponseSinks=DmpResponseSinks(id_short="ResponseSinks", value=[response_sink("Outputs", operation_ref(name))]),
    )


def _packml_invocations(interface: str) -> list[AimcMappingConfiguration]:
    return [
        AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=[SourcesItem(
                id_short=name, SourceId=SourceId(value=name), Source=Source(value=operation_ref(name)),
            )]),
            Sinks=Sinks(value=[SinksItem(
                id_short=name, SinkId=SinkId(value=name),
                Sink=Sink(value=affordance_ref(interface, "actions", name)),
            )]),
            Transformation=Transformation(value=(
                f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.{name}.Uuid }} }} end"
            )),
            **({} if name in INVOKE_ONLY_SKILLS else command_reply(interface, name)),
        ) for name in PACKML_SKILLS
    ]


def _state_sinks() -> Sinks:
    return Sinks(value=[SinksItem(
        id_short=name, SinkId=SinkId(value=name), Sink=Sink(value=variable_ref(name)),
    ) for name in ("PackMLState", "OccupationState")])


# The occupation queue is written as JSON array text: the variable is a string
# Property, and an empty Lua table would not encode as an array.
_STATE_TRANSFORMATION = """function aimc_main(sources)
    local queue = {queue} or {{}}
    return {{
        PackMLState = {state},
        OccupationState = (#queue == 0) and "[]" or json.encode(queue),
    }}
end
"""


class OperationalMqttMappings(Aimc):
    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations(value=[
        AimcMappingConfiguration(
            id_short="MQTT", DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=[SourcesItem(
                id_short="StationState", SourceId=SourceId(value="StationState"),
                Source=Source(value=affordance_ref(MQTT_INTERFACE, "properties", "StationState")),
            )]),
            Sinks=_state_sinks(),
            Transformation=Transformation(value=_STATE_TRANSFORMATION.format(
                queue="sources.StationState.ProcessQueue", state="sources.StationState.State",
            )),
        ),
        *_packml_invocations(MQTT_INTERFACE),
    ])


class OperationalOpcuaMappings(Aimc):
    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations(value=[
        AimcMappingConfiguration(
            id_short="OPCUA", DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
            Sources=Sources(value=[SourcesItem(
                id_short=name, SourceId=SourceId(value=name),
                Source=Source(value=affordance_ref(OPCUA_INTERFACE, "properties", name)),
            ) for name in ("State", "ProcessQueue")]),
            Sinks=_state_sinks(),
            Transformation=Transformation(value=_STATE_TRANSFORMATION.format(
                queue="sources.ProcessQueue", state="sources.State",
            )),
        ),
        *_packml_invocations(OPCUA_INTERFACE),
    ])

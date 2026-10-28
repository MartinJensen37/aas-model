"""Typed, independently copied defaults of the AAU planar-shuttle type."""

from aas_pydantic import Property
from aas_pydantic import Capability, ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilityDescription, CapabilityRealizedBy,
    CapabilityRelations, CapabilitySet,
)

from aas_model.constants import CSSX, INVOCATION_URL_TEMPLATE, SCHEMA_BASE
from aas_model.json_schema_aid import load_schema
from aas_model.resource_template.asset_interfaces_description import (
    MQTT_INTERFACE, affordance_ref, mqtt_action, mqtt_property,
)
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    mapping_configuration, operation_sources, series_segment_ref, sink, source, variable_ref,
)
from aas_model.resource_template.control_component_instance import skill_ref
from aas_model.resource_template.operational import (
    action_member_ref,
    OperationalMqttControlComponent, OperationalMqttInterfaces,
    OperationalMqttMappings, operational_variables, command_reply,
)
from aas_model.submodel_templates.control_component_instance import (
    EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, OptionalVariable,
    SkillInterfaceRelationship, SkillOperation,
)
from aas_model.submodel_templates.variables import MeasurementsGroup, VariableItem, VariableProp
from aas_model.submodel_templates.time_series import record_field, time_series


planar_interfaces = OperationalMqttInterfaces(id_short="AssetInterfacesDescription")
_interaction = planar_interfaces.InterfaceTemplateForMQTT[MQTT_INTERFACE].InteractionMetadata
_url = f"{SCHEMA_BASE}/moveToPosition.schema.json"
# The device's motion topics are CMD/XYMotion and DATA/XYMotion.
_interaction.actions.property_name["MoveToPosition"] = mqtt_action(
    "MoveToPosition", synchronous=False, input_schema=load_schema(_url), input_schema_url=_url,
    topic="XYMotion",
)
_url = f"{SCHEMA_BASE}/positionStamped.schema.json"
_interaction.properties.property_name["Location"] = mqtt_property(
    "Location", "DATA/Location", schema=load_schema(_url), schema_url=_url,
)


planar_control = OperationalMqttControlComponent(id_short="ControlComponentInstance")
planar_control.Skills.Skill["MoveToPosition"] = ExtendedSkill(
    id_short="MoveToPosition",
    interface_reference=ReferenceElement(
        semantic_id=EXTENDED_SKILL_INTERFACE_REF,
        value=affordance_ref(MQTT_INTERFACE, "actions", "MoveToPosition"),
    ),
    operation=SkillOperation(
        id_short="operation",
        qualifiers=[
            Qualifier(
                type_="invocationDelegation", kind="ConceptQualifier", value_type="xs:string",
                value=INVOCATION_URL_TEMPLATE,
            ),
            Qualifier(
                type_="Asynchronous", kind="ConceptQualifier", value_type="xs:string", value="false",
            ),
        ],
        # ProductID is not sent to the device; the reply echoes the caller's value.
        in_output_variable=[
            Property(id_short="Uuid", description="The UUID of the command"),
            Property(id_short="ProductID", description="The product the shuttle carries",
                     qualifiers=[OptionalVariable()]),
        ],
        input_variable=[
            Property(id_short=axis, value_type="xs:double", value="0.0")
            for axis in ("X", "Y", "Theta")
        ],
        output_variable=[
            Property(id_short="State", description="The state of the command being executed"),
            Property(id_short="Outcome", value_type="xs:integer", value="0", qualifiers=[OptionalVariable()]),
        ],
    ),
)
planar_control.Endpoints.Endpoint["MoveToPosition"] = SkillInterfaceRelationship(
    id_short="MoveToPosition",
    first=skill_ref("MoveToPosition"),
    second=affordance_ref(MQTT_INTERFACE, "actions", "MoveToPosition"),
)


planar_capabilities = CapabilityDescription(
    id_short="CapabilityDescription",
    CapabilitySet={"Transport": CapabilitySet(
        id_short="Transport",
        CapabilityContainer={"MoveToPosition": CapabilityContainer(
            id_short="MoveToPosition",
            Capability=Capability(id_short="Capability", semantic_id=f"{CSSX}#MoveToPosition"),
            CapabilityRelations=CapabilityRelations(
                id_short="CapabilityRelations",
                CapabilityRealizedBy={"RealizedBy_MoveToPosition": CapabilityRealizedBy(
                    id_short="RealizedBy_MoveToPosition",
                    first=ModelReference(key=(
                        Key(type_="Submodel", value="{aas_id}/submodels/CapabilityDescription"),
                        Key(type_="SubmodelElementCollection", value="Transport"),
                        Key(type_="SubmodelElementCollection", value="MoveToPosition"),
                        Key(type_="Capability", value="Capability"),
                    )),
                    second=skill_ref("MoveToPosition"),
                )},
            ),
        )},
    )},
)


planar_variables = operational_variables()
planar_variables.variable.update({
    "Location": VariableItem(id_short="Location", value={
        axis: VariableProp(id_short=axis, value_type="xs:double", value="0.0")
        for axis in ("x", "y", "yaw")
    }),
    "PositionX": VariableProp(id_short="PositionX", value_type="xs:double", value="0.0"),
    "PositionY": VariableProp(id_short="PositionY", value_type="xs:double", value="0.0"),
})
# The shuttle's track: one row per reported position into Variables/Measurements/Location.
planar_variables.Measurements = MeasurementsGroup(value={"Location": time_series(
    name="Shuttle position", measurement="transport_position",
    fields={axis: record_field("xs:double") for axis in ("x", "y", "yaw")},
)})


planar_mappings = OperationalMqttMappings(id_short="AssetInterfacesMappingConfiguration")
planar_mappings.MappingConfigurations.value.extend([
    mapping_configuration(
        id_short="MoveToPosition",
        sources=operation_sources("MoveToPosition", ["Uuid", "ProductID", "X", "Y", "Theta"]),
        sinks=[sink("MoveToPosition", action_member_ref(MQTT_INTERFACE, "MoveToPosition", "input"))],
        transformation="""function aimc_main(sources)
    return { MoveToPosition = { Uuid = sources.Uuid, Position = {sources.X, sources.Y, sources.Theta} } }
end
""",
    ).model_copy(update=command_reply(
        MQTT_INTERFACE, "MoveToPosition", outputs=("Uuid", "State", "Outcome"), echoed=("ProductID",),
    )),
    mapping_configuration(
        id_short="ObserveLocation",
        sources=[source("Location", affordance_ref(MQTT_INTERFACE, "properties", "Location"))],
        sinks=[
            sink(f"Location_{axis}", ModelReference(key=(
                Key(type_="Submodel", value="{aas_id}/submodels/Variables"),
                Key(type_="SubmodelElementCollection", value="Location"),
                Key(type_="Property", value=axis),
            ))) for axis in ("x", "y", "yaw")
        ] + [sink(name, variable_ref(name)) for name in ("PositionX", "PositionY")],
        transformation="""function aimc_main(sources)
    local position = sources.Location.Position
    return {
        Location_x = position[1], Location_y = position[2], Location_yaw = position[3] or 0.0,
        PositionX = position[1], PositionY = position[2],
    }
end
""",
    ),
    mapping_configuration(
        id_short="LocationHistory",
        sources=[source("Location", affordance_ref(MQTT_INTERFACE, "properties", "Location"))],
        sinks=[sink("Live", series_segment_ref("Measurements", "Location"))],
        transformation="""function aimc_main(sources)
    local position = sources.Location.Position
    return { Live = { x = position[1], y = position[2], yaw = position[3] or 0.0 } }
end
""",
    ),
])

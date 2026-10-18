"""Typed, independently copied defaults of the AAU planar-shuttle type."""

from aas_pydantic import Capability, ExternalReference, Key, ModelReference, Qualifier, ReferenceElement
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilityDescription, CapabilityRealizedBy,
    CapabilityRelations, CapabilitySet,
)

from aas_model.constants import CSSX, INVOCATION_ORIGIN, SCHEMA_BASE
from aas_model.json_schema_aid import load_schema
from aas_model.resource_template.asset_interfaces_description import mqtt_action, mqtt_property
from aas_model.resource_template.asset_interfaces_mapping_configuration import (
    _mqtt_action_ref, _property_ref, _variable_ref, mapping_configuration,
    operation_ref, sink, source,
)
from aas_model.resource_template.control_component_instance import native_action_ref, skill_ref
from aas_model.resource_template.operational import (
    OperationalControlComponent, OperationalMqttInterfaces,
    OperationalMqttMappings, OperationalVariables,
)
from aas_model.submodel_templates.control_component_instance import (
    EXTENDED_SKILL_INTERFACE_REF, ExtendedSkill, OperationVariableProp,
    SkillInterfaceRelationship, SkillOperation,
)
from aas_model.submodel_templates.variables import VariableItem, VariableProp


planar_interfaces = OperationalMqttInterfaces(id_short="AssetInterfacesDescription")
_interaction = planar_interfaces.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata
_url = f"{SCHEMA_BASE}/moveToPosition.schema.json"
_interaction.actions.property_name["MoveToPosition"] = mqtt_action(
    "MoveToPosition", synchronous=False, input_schema=load_schema(_url), input_schema_url=_url,
)
_url = f"{SCHEMA_BASE}/positionStamped.schema.json"
_interaction.properties.property_name["Location"] = mqtt_property(
    "Location", "DATA/Location", schema=load_schema(_url), schema_url=_url,
)
_url = f"{SCHEMA_BASE}/productId.schema.json"
_interaction.properties.property_name["ProductID"] = mqtt_property(
    "ProductID", "DATA/ProductId", schema=load_schema(_url), schema_url=_url,
)


planar_control = OperationalControlComponent(id_short="ControlComponentInstance")
planar_control.Skills.Skill["MoveToPosition"] = ExtendedSkill(
    id_short="MoveToPosition",
    interface_reference=ReferenceElement(
        semantic_id=EXTENDED_SKILL_INTERFACE_REF,
        value=native_action_ref("MoveToPosition"),
    ),
    operation=SkillOperation(
        id_short="operation",
        qualifiers=[
            Qualifier(
                type_="invocationDelegation", kind="ConceptQualifier", value_type="xs:string",
                value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}",
            ),
            Qualifier(
                type_="Asynchronous", kind="ConceptQualifier", value_type="xs:string", value="false",
            ),
        ],
        in_output_variable=[OperationVariableProp(id_short="Uuid", description="The UUID of the command")],
        input_variable=[
            OperationVariableProp(id_short=axis, value_type="xs:double", value="0.0")
            for axis in ("X", "Y", "Theta")
        ],
        output_variable=[
            OperationVariableProp(id_short="State", description="The state of the command being executed"),
            OperationVariableProp(id_short="Outcome", value_type="xs:integer", value="0"),
        ],
    ),
)
planar_control.Endpoints.Endpoint["MoveToPosition"] = SkillInterfaceRelationship(
    id_short="MoveToPosition",
    first=skill_ref("MoveToPosition"),
    second=native_action_ref("MoveToPosition"),
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
                    second=ExternalReference(key=(Key(
                        type_="GlobalReference",
                        value="{aas_id}/submodels/ControlComponentInstance/Skills/MoveToPosition",
                    ),)),
                )},
            ),
        )},
    )},
)


planar_variables = OperationalVariables(id_short="Variables")
planar_variables.variable.update({
    "Location": VariableItem(id_short="Location", value={
        axis: VariableProp(id_short=axis, value_type="xs:double", value="0.0")
        for axis in ("x", "y", "yaw")
    }),
    "PositionX": VariableProp(id_short="PositionX", value_type="xs:double", value="0.0"),
    "PositionY": VariableProp(id_short="PositionY", value_type="xs:double", value="0.0"),
    "ProductID": VariableProp(id_short="ProductID"),
})


planar_mappings = OperationalMqttMappings(id_short="AssetInterfacesMappingConfiguration")
planar_mappings.MappingConfigurations.value.extend([
    mapping_configuration(
        id_short="MoveToPosition",
        sources=[source("MoveToPosition", operation_ref("MoveToPosition"))],
        sinks=[sink("MoveToPosition", _mqtt_action_ref("MoveToPosition"))],
        transformation="""function aimc_main(sources)
    local op = sources.MoveToPosition
    return { MoveToPosition = { Uuid = op.Uuid, Position = {op.X, op.Y, op.Theta} } }
end
""",
    ),
    mapping_configuration(
        id_short="ObserveLocation",
        sources=[source("Location", _property_ref("Location"))],
        sinks=[
            sink(f"Location_{axis}", ModelReference(key=(
                Key(type_="Submodel", value="{aas_id}/submodels/Variables"),
                Key(type_="SubmodelElementCollection", value="Location"),
                Key(type_="Property", value=axis),
            ))) for axis in ("x", "y", "yaw")
        ] + [sink(name, _variable_ref(name)) for name in ("PositionX", "PositionY")],
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
        id_short="ObserveProductID",
        sources=[source("ProductID", _property_ref("ProductID"))],
        sinks=[
            sink("ProductID", _variable_ref("ProductID")),
            sink("ProductIDParameter", ModelReference(key=(
                Key(type_="Submodel", value="{aas_id}/submodels/Parameters"),
                Key(type_="Property", value="ProductID"),
            ))),
        ],
        transformation="""function aimc_main(sources)
    return { ProductID = sources.ProductID.ProductId, ProductIDParameter = sources.ProductID.ProductId }
end
""",
    ),
])

"""The migrated catalog is typed, independent, and usable without legacy YAML."""

import json

import pytest
from pydantic import BaseModel
from pydantic import ValidationError

from aas_model import Resource, build_from_model, inject_ids
from aas_model.constants import SCHEMA_BASE
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, EntryNode, HierarchicalStructures,
)
from aas_model.resource_template import (
    Station, MqttOperationalStation, ProcessingStation, HandlingStation, TransportResource,
    Shuttle, SoftwareResource, CompositeResource, PhysicalResource, OperationalResource,
)
from aas_model.resource_template.transport import PlanarShuttle
from aas_model.resource_template.software import MqttSoftwareResource
from aas_pydantic import ExternalReference, Key, ModelReference
from aas_pydantic.submodel_templates.capability_description import CapabilityRealizedBy
from aas_pydantic.convert_pydantic_model import _make_basyx_reference
from test_resource import _document


CATALOG_NAMES = {
    "aauFillingLine", "cytivaCapping", "imaDispensing", "imaLoadingSystem",
    "omronCamera", "optimaUnloading", "orchestrator", "planarShuttle1",
    "planarShuttle2", "planarShuttle3", "planarTable", "productionPlanner",
    "syntegonStoppering",
}


def test_catalog_covers_every_legacy_resource():
    assert set(RESOURCE_FACTORIES) == CATALOG_NAMES
    identities = [factory().id for factory in RESOURCE_FACTORIES.values()]
    assert len(set(identities)) == len(identities)
    assert all(
        type(factory()).__module__.startswith("aas_model.resource_template.")
        for factory in RESOURCE_FACTORIES.values()
    )


@pytest.mark.parametrize("name", sorted(CATALOG_NAMES))
def test_instances_round_trip_through_specific_and_registration_types(name):
    resource = RESOURCE_FACTORIES[name]()
    encoded = resource.model_dump_json()
    restored = type(resource).model_validate_json(encoded)
    base_restored = Resource.model_validate_json(encoded)

    assert restored.model_dump(mode="json") == json.loads(encoded)
    assert base_restored.model_dump(mode="json") == json.loads(encoded)
    expected = _document(build_from_model(resource))
    assert _document(build_from_model(restored)) == expected
    assert _document(build_from_model(base_restored)) == expected
    assert resource.model_dump_json() == encoded


@pytest.mark.parametrize("name", sorted(CATALOG_NAMES))
def test_each_factory_returns_independent_defaults(name):
    first = RESOURCE_FACTORIES[name]()
    second = RESOURCE_FACTORIES[name]()
    before = second.model_dump_json()
    first.parameters.parameter.clear()
    first.variables.variable.clear()
    first.control_component_instance.Skills.Skill.clear()
    first.asset_interfaces_description.InterfaceTemplateForMQTT.clear()
    first.asset_interfaces_mapping_configuration.MappingConfigurations.value.clear()
    assert second.model_dump_json() == before
    assert RESOURCE_FACTORIES[name]().model_dump_json() == before


@pytest.mark.parametrize("resource_type", [
    Resource, Station, MqttOperationalStation, ProcessingStation, HandlingStation, TransportResource,
    Shuttle, PlanarShuttle, SoftwareResource, MqttSoftwareResource, CompositeResource,
])
def test_resource_types_have_coherent_defaults_and_preserve_empty_imports(resource_type):
    kwargs = {"hierarchical_structures": HierarchicalStructures(
        id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
        EntryNode=EntryNode(id_short="EntryNode", global_asset_id="Example"),
    )} if resource_type is CompositeResource else {}
    resource = resource_type(id_short="Example", **kwargs)
    assert isinstance(resource, Resource)
    for name, skill in resource.control_component_instance.Skills.Skill.items():
        actions = resource.asset_interfaces_description.InterfaceTemplateForMQTT[
            "interface_mqtt"
        ].InteractionMetadata.actions.property_name
        assert name in actions
        invocation = next(q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation")
        assert invocation.value == f"http://dmp:8080/operations/Example/{name}"
    resource.control_component_instance.Skills.Skill.clear()
    resource.asset_interfaces_description.InterfaceTemplateForMQTT.clear()
    resource.variables.variable.clear()
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.clear()
    encoded = resource.model_dump_json()
    assert resource_type.model_validate_json(encoded).model_dump_json() == encoded


def _references(value):
    if isinstance(value, ModelReference):
        yield value
    elif isinstance(value, BaseModel):
        for name in type(value).model_fields:
            yield from _references(getattr(value, name))
    elif isinstance(value, dict):
        for child in value.values():
            yield from _references(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _references(child)


@pytest.mark.parametrize("name", sorted(CATALOG_NAMES))
def test_all_local_runtime_references_resolve(name):
    resource = RESOURCE_FACTORIES[name]()
    store = build_from_model(resource)
    resolved = resource.model_copy(deep=True)
    inject_ids(resolved)
    for reference in _references(resolved):
        root = reference.key[0].value
        # CCI's optional external type definition is inherited from Resource;
        # it is not a runtime source/sink or part of this instance's store.
        if root == f"{resource.id}/submodels/ControlComponentType":
            continue
        if root.startswith(resource.id):
            assert _make_basyx_reference(reference).resolve(store) is not None


def test_filling_line_and_table_topology_matches_catalog_identities():
    line = RESOURCE_FACTORIES["aauFillingLine"]()
    table = RESOURCE_FACTORIES["planarTable"]()
    station_names = (
        "syntegonStoppering", "cytivaCapping", "imaDispensing", "imaLoadingSystem",
        "optimaUnloading", "omronCamera",
    )
    stations = [RESOURCE_FACTORIES[name]() for name in station_names]
    assert set(line.hierarchical_structures.EntryNode.Node) == {
        station.id_short for station in stations
    } | {table.id_short}
    for station in stations:
        assert station.hierarchical_structures.ArcheType.value == "OneUp"
        assert set(station.hierarchical_structures.EntryNode.Node) == {line.id_short}
    for number in (1, 2, 3):
        shuttle = RESOURCE_FACTORIES[f"planarShuttle{number}"]()
        assert shuttle.id_short in table.hierarchical_structures.EntryNode.Node
        assert set(shuttle.hierarchical_structures.EntryNode.Node) == {table.id_short}
        assert isinstance(shuttle, TransportResource)


def test_system_type_requires_its_hierarchical_structure():
    with pytest.raises(ValidationError, match="hierarchical_structures"):
        CompositeResource(id_short="IncompleteSystem")


def test_motion_schema_operation_and_mapping_describe_the_same_payload():
    shuttle = RESOURCE_FACTORIES["planarShuttle1"]()
    skill = shuttle.control_component_instance.Skills.Skill["MoveToPosition"]
    assert [(v.id_short, v.value_type) for v in skill.operation.input_variable] == [
        ("X", "xs:double"), ("Y", "xs:double"), ("Theta", "xs:double"),
    ]
    action = shuttle.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name["MoveToPosition"]
    assert f"{SCHEMA_BASE}/moveToPosition.schema.json" in action.input.supplemental_semantic_ids
    mapping = next(
        m for m in shuttle.asset_interfaces_mapping_configuration.MappingConfigurations.value
        if m.id_short == "MoveToPosition"
    )
    assert b"Position = {op.X, op.Y, op.Theta}" in mapping.Transformation.value
    assert b"Uuid = op.Uuid" in mapping.Transformation.value


def test_extra_station_telemetry_has_variables_and_live_mappings():
    dispensing = RESOURCE_FACTORIES["imaDispensing"]()
    camera = RESOURCE_FACTORIES["omronCamera"]()
    for resource, names in ((dispensing, {"Weight"}), (camera, {"Image", "QualityResult"})):
        assert names <= resource.variables.variable.keys()
        mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
        assert {f"Observe{name}" for name in names} <= {m.id_short for m in mappings}


def test_software_commands_include_their_native_payload_inputs():
    planner = RESOURCE_FACTORIES["productionPlanner"]()
    assert {v.id_short for v in planner.control_component_instance.Skills.Skill["Plan"].operation.input_variable} == {
        "Assets", "Order",
    }
    assert set(planner.variables.variable) == {"PackMLState"}
    assert "StationState" in planner.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.properties.property_name
    orchestrator = RESOURCE_FACTORIES["orchestrator"]()
    props = orchestrator.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.properties.property_name
    assert "State" in props
    assert "StationState" not in props
    mappings = orchestrator.asset_interfaces_mapping_configuration.MappingConfigurations.value
    assert "MQTT" not in {m.id_short for m in mappings}
    assert "ObserveState" in {m.id_short for m in mappings}
    for name in ("Start", "Unsuspend"):
        inputs = orchestrator.control_component_instance.Skills.Skill[name].operation.input_variable
        assert [v.id_short for v in inputs] == ["Process"]


def test_static_location_does_not_advertise_a_nonexistent_live_interface():
    resource = Station(id_short="Static")
    location = resource.parameters.parameter["Location"]
    assert all(getattr(location, axis).interface_reference is None for axis in ("x", "y", "yaw"))


@pytest.mark.parametrize("template", [MqttOperationalStation])
def test_generic_templates_do_not_claim_instance_specific_operations_or_telemetry(template):
    resource = template(id_short="Generic")
    interaction = resource.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata
    assert set(interaction.actions.property_name) == {"Halt", "Occupy", "Release"}
    assert set(interaction.properties.property_name) == {"StationState"}
    assert set(resource.control_component_instance.Skills.Skill) == {"Halt", "Occupy", "Release"}
    assert set(resource.variables.variable) == {"PackMLState", "OccupationState"}
    assert resource.capability_description.CapabilitySet == {}


@pytest.mark.parametrize("template", [Resource, Station, SoftwareResource, CompositeResource])
def test_non_station_resources_do_not_inherit_physical_location_or_station_skills(template):
    kwargs = {"hierarchical_structures": HierarchicalStructures(
        id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
        EntryNode=EntryNode(id_short="EntryNode", global_asset_id="Generic"),
    )} if template is CompositeResource else {}
    resource = template(id_short="Generic", **kwargs)
    assert resource.asset_interfaces_description.InterfaceTemplateForMQTT == {} or (
        resource.asset_interfaces_description.InterfaceTemplateForMQTT[
            "interface_mqtt"
        ].InteractionMetadata.actions.property_name == {}
    )
    assert resource.control_component_instance.Skills.Skill == {}
    assert resource.variables.variable == {}
    assert ("Location" in resource.parameters.parameter) is (template is Station)


def test_physical_and_operational_inheritance_is_declared_at_the_right_level():
    physical = PhysicalResource(id_short="Pump")
    operational = OperationalResource(id_short="Shuttle")
    assert "Location" in physical.parameters.parameter
    assert physical.control_component_instance.Skills.Skill == {}
    assert operational.control_component_instance.Skills.Skill == {}
    lab = MqttOperationalStation(id_short="Lab")
    assert set(lab.control_component_instance.Skills.Skill) == {
        "Halt", "Occupy", "Release",
    }
    assert set(lab.variables.variable) == {"PackMLState", "OccupationState"}
    assert isinstance(RESOURCE_FACTORIES["planarShuttle1"](), PhysicalResource)


def test_dispensing_type_declares_capability_but_not_vendor_skill_or_weight():
    from aas_model.resource_template.stations import DispensingStation

    station = DispensingStation(id_short="GenericDispensing")
    assert set(station.capability_description.CapabilitySet["Processing"].CapabilityContainer) == {"Dispensing"}
    assert "Weight" not in station.variables.variable
    assert "Dispensing" not in station.control_component_instance.Skills.Skill
    assert station.asset_interfaces_description.InterfaceTemplateForMQTT == {}
    concrete = RESOURCE_FACTORIES["imaDispensing"]()
    assert "Dispensing" in concrete.control_component_instance.Skills.Skill
    action = concrete.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name["Dispensing"]
    assert f"{SCHEMA_BASE}/command.schema.json" in action.input.supplemental_semantic_ids


def test_direct_typed_defaults_are_independent_across_resources():
    from aas_model.resource_template.stations import MqttOperationalStation, StopperingStation

    assert MqttOperationalStation.model_fields["variables"].default_factory is None
    assert MqttOperationalStation.model_fields["control_component_instance"].default_factory is None
    assert StopperingStation.model_fields["capability_description"].default_factory is None

    first = MqttOperationalStation(id_short="First")
    second = MqttOperationalStation(id_short="Second")
    first.variables.variable["PackMLState"].value = "RUNNING"
    first.control_component_instance.Skills.Skill.clear()
    assert second.variables.variable["PackMLState"].value != "RUNNING"
    assert "Halt" in second.control_component_instance.Skills.Skill

    first_capability = StopperingStation(id_short="First")
    second_capability = StopperingStation(id_short="Second")
    first_capability.capability_description.CapabilitySet["Processing"].CapabilityContainer.clear()
    assert "Stoppering" in second_capability.capability_description.CapabilitySet["Processing"].CapabilityContainer


def test_graph_validation_rejects_invalid_direct_dict_insertions_before_aas_export():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    resource.control_component_instance.Skills.Skill["Invalid"] = 42
    with pytest.warns(UserWarning, match="Pydantic serializer warnings"):
        with pytest.raises(ValidationError):
            build_from_model(resource)


def test_shuttle_instances_use_the_shared_shuttle_type():
    for name in ("planarShuttle1", "planarShuttle2", "planarShuttle3"):
        assert type(RESOURCE_FACTORIES[name]()) is PlanarShuttle


def test_orchestrator_http_interface_is_not_inherited_by_other_software():
    orchestrator = RESOURCE_FACTORIES["orchestrator"]()
    http = orchestrator.asset_interfaces_description.InterfaceTemplateForHTTP["interface_http"]
    assert set(http.InteractionMetadata.actions.property_name) == {"Start", "Stop", "Reset"}
    assert "Health" in http.InteractionMetadata.properties.property_name
    assert SoftwareResource(id_short="Generic").asset_interfaces_description.InterfaceTemplateForHTTP == {}
    assert RESOURCE_FACTORIES["productionPlanner"]().asset_interfaces_description.InterfaceTemplateForHTTP == {}


@pytest.mark.parametrize("name", sorted(CATALOG_NAMES))
def test_factory_authored_skills_have_finalized_invocations_and_empty_imports_stay_empty(name):
    resource = RESOURCE_FACTORIES[name]()
    for skill_name, skill in resource.control_component_instance.Skills.Skill.items():
        invocation = next(q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation")
        assert invocation.value == f"http://dmp:8080/operations/{resource.id_short}/{skill_name}"
    resource.control_component_instance.Skills.Skill.clear()
    resource.asset_interfaces_description.InterfaceTemplateForMQTT.clear()
    resource.variables.variable.clear()
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.clear()
    encoded = resource.model_dump_json()
    assert Resource.model_validate_json(encoded).model_dump_json() == encoded


@pytest.mark.parametrize("names, template, group", [
    (("syntegonStoppering", "cytivaCapping", "imaDispensing"), ProcessingStation, "Processing"),
    (("imaLoadingSystem", "optimaUnloading"), HandlingStation, "Handling"),
])
def test_related_stations_share_their_type_and_capability_group(names, template, group):
    for name in names:
        resource = RESOURCE_FACTORIES[name]()
        assert isinstance(resource, template)
        assert set(resource.capability_description.CapabilitySet) == {group}


def test_capability_realization_is_explicit_and_not_a_skill_naming_rule():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    relations = resource.capability_description.CapabilitySet[
        "Processing"
    ].CapabilityContainer["Dispensing"].CapabilityRelations.CapabilityRealizedBy
    assert relations["RealizedBy_Dispensing"].first.key[-1].value == "Capability"
    assert relations["RealizedBy_Dispensing"].second.key[-1].value.endswith(
        "/ControlComponentInstance/Skills/Dispensing"
    )
    relations["RealizedBy_AlternativeImplementation"] = CapabilityRealizedBy(
        id_short="RealizedBy_AlternativeImplementation",
        first=relations["RealizedBy_Dispensing"].first.model_copy(deep=True),
        second=ExternalReference(key=(Key(
            type_="GlobalReference",
            value="{aas_id}/submodels/ControlComponentInstance/Skills/AlternativeImplementation",
        ),)),
    )
    assert "RealizedBy_AlternativeImplementation" in relations


@pytest.mark.parametrize("name, group, capability, skill", [
    ("syntegonStoppering", "Processing", "Stoppering", "Stoppering"),
    ("cytivaCapping", "Processing", "Capping", "Capping"),
    ("imaDispensing", "Processing", "Dispensing", "Dispensing"),
    ("imaLoadingSystem", "Handling", "Loading", "Loading"),
    ("optimaUnloading", "Handling", "Unloading", "Unloading"),
    ("optimaUnloading", "Handling", "Scrap", "Scrap"),
    ("omronCamera", "Inspection", "Capture", "Capture"),
    ("planarShuttle1", "Transport", "MoveToPosition", "MoveToPosition"),
    ("orchestrator", "Coordination", "Orchestrate", "Start"),
    ("productionPlanner", "Planning", "Plan", "Plan"),
])
def test_capabilities_explicitly_link_to_the_selected_implementation(name, group, capability, skill):
    resource = RESOURCE_FACTORIES[name]()
    container = resource.capability_description.CapabilitySet[group].CapabilityContainer[capability]
    assert skill in resource.control_component_instance.Skills.Skill
    assert container.CapabilityRelations is not None
    relation = next(iter(container.CapabilityRelations.CapabilityRealizedBy.values()))
    assert relation.first.key[-1].value == "Capability"
    assert relation.second.key[0].value.endswith(f"/ControlComponentInstance/Skills/{skill}")
    exported = resource.model_copy(deep=True)
    inject_ids(exported)
    target = exported.capability_description.CapabilitySet[group].CapabilityContainer[
        capability
    ].CapabilityRelations.CapabilityRealizedBy[relation.id_short]
    assert target.first.key[0].value == f"{resource.id}/submodels/CapabilityDescription"
    assert target.second.key[0].value == (
        f"{resource.id}/submodels/ControlComponentInstance/Skills/{skill}"
    )

"""Typed AAS resource hierarchy and reusable reference/schema utilities."""

from .asset import Resource, ResourceTypeAAS
from .asset_interfaces_description import (
    MQTT_INTERFACE, OPCUA_INTERFACE, affordance_ref,
    mqtt_action, mqtt_property, opcua_action, opcua_property,
)
from .control_component_instance import (
    ResourceControlComponentInstance, extended_skill,
    skill_operation, skill_interface_relationship, skill_ref,
)
from .asset_interfaces_mapping_configuration import (
    mapping_configuration,
    operation_ref,
    variable_ref,
    response_sink,
    response_source,
)
from .parameters import Position, ResourceParameters
from .physical import PhysicalResource, OperationalResource
from .stations import (
    Station, MqttOperationalStation, OpcuaOperationalStation, ProcessingStation, HandlingStation,
)
from .transport import TransportResource, Shuttle
from .software import SoftwareResource
from .systems import CompositeResource

__all__ = [
    "Resource",
    "ResourceTypeAAS",
    "PhysicalResource",
    "OperationalResource",
    "Station",
    "MqttOperationalStation",
    "OpcuaOperationalStation",
    "ProcessingStation",
    "HandlingStation",
    "TransportResource",
    "Shuttle",
    "SoftwareResource",
    "CompositeResource",
    "MQTT_INTERFACE",
    "OPCUA_INTERFACE",
    "affordance_ref",
    "mqtt_action",
    "mqtt_property",
    "opcua_action",
    "opcua_property",
    "ResourceControlComponentInstance",
    "extended_skill",
    "skill_operation",
    "skill_interface_relationship",
    "skill_ref",
    "mapping_configuration",
    "operation_ref",
    "variable_ref",
    "response_source",
    "response_sink",
    "Position",
    "ResourceParameters",
]

"""Resource hierarchy with type-level capabilities and lab-specific bindings."""

from aas_model.constants import CSSX
from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
from aas_model.resource_template.physical import OperationalResource
from aas_model.submodel_templates.variables import Variables
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates import Aimc
from aas_model.resource_template.control_component_instance import ResourceControlComponentInstance
from aas_model.resource_template.operational import (
    OperationalMqttInterfaces, OperationalMqttControlComponent, OperationalMqttMappings,
    OperationalOpcuaInterfaces, OperationalOpcuaControlComponent, OperationalOpcuaMappings,
    operational_variables,
)
from .submodels import (
    StopperingCapabilities, CappingCapabilities, DispensingCapabilities,
    LoadingCapabilities, UnloadingCapabilities, InspectionCapabilities,
)


class Station(OperationalResource):
    """Physical workstation, independent of the native interface protocol."""

    asset_type: str = f"{CSSX}#Station"

class MqttOperationalStation(Station):
    """Station with the shared PackML contract over MQTT."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalMqttInterfaces(
        id_short="AssetInterfacesDescription",
    )
    control_component_instance: ResourceControlComponentInstance = OperationalMqttControlComponent(
        id_short="ControlComponentInstance",
    )
    asset_interfaces_mapping_configuration: Aimc = OperationalMqttMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = operational_variables()


class OpcuaOperationalStation(Station):
    """Station with the shared PackML contract over OPC UA."""

    asset_interfaces_description: DmpAssetInterfacesDescription = OperationalOpcuaInterfaces(
        id_short="AssetInterfacesDescription",
    )
    control_component_instance: ResourceControlComponentInstance = OperationalOpcuaControlComponent(
        id_short="ControlComponentInstance",
    )
    asset_interfaces_mapping_configuration: Aimc = OperationalOpcuaMappings(
        id_short="AssetInterfacesMappingConfiguration",
    )
    variables: Variables = operational_variables()


class ProcessingStation(Station):
    """A station that changes a product; concrete stations declare their skills."""

    asset_type: str = f"{CSSX}#ProcessingStation"

class HandlingStation(Station):
    """A station that loads, unloads, or otherwise handles a product."""

    asset_type: str = f"{CSSX}#HandlingStation"



class StopperingStation(ProcessingStation):
    asset_type: str = f"{CSSX}#StopperingSystem"
    capability_description: CapabilityDescription = StopperingCapabilities(id_short="CapabilityDescription")


class CappingStation(ProcessingStation):
    asset_type: str = f"{CSSX}#CappingSystem"
    capability_description: CapabilityDescription = CappingCapabilities(id_short="CapabilityDescription")


class DispensingStation(ProcessingStation):
    asset_type: str = f"{CSSX}#DispensingSystem"
    capability_description: CapabilityDescription = DispensingCapabilities(id_short="CapabilityDescription")


class LoadingStation(HandlingStation):
    asset_type: str = f"{CSSX}#LoadingSystem"
    capability_description: CapabilityDescription = LoadingCapabilities(id_short="CapabilityDescription")


class UnloadingStation(HandlingStation):
    asset_type: str = f"{CSSX}#UnloadingSystem"
    capability_description: CapabilityDescription = UnloadingCapabilities(id_short="CapabilityDescription")


class InspectionStation(Station):
    asset_type: str = f"{CSSX}#QualityControlSystem"
    capability_description: CapabilityDescription = InspectionCapabilities(id_short="CapabilityDescription")

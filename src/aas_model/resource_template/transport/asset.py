"""Transport AAS types with explicit, typed submodel fields."""

from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates import Aimc
from aas_model.resource_template.control_component_instance import ResourceControlComponentInstance
from aas_model.submodel_templates.variables import Variables

from aas_model.constants import CSSX
from aas_model.resource_template.physical import PhysicalResource
from aas_model.resource_template.parameters import Position, ResourceParameters

from . import submodels


class TransportResource(PhysicalResource):
    """Protocol-neutral physical transport resource."""
    asset_type: str = f"{CSSX}#TransportSystem"


class Shuttle(TransportResource):
    """Protocol-neutral shuttle; payload and product tracking are specialized."""
    asset_type: str = f"{CSSX}#Shuttle"


class PlanarShuttle(Shuttle):
    """MQTT-backed planar implementation of the shared shuttle semantics.

    Native Position arrays and operation X/Y/Theta use millimetres and radians.
    """
    asset_type: str = f"{CSSX}#PlanarTableShuttle"
    parameters: ResourceParameters = ResourceParameters(
        id_short="Parameters",
        parameter={"Location": Position()},
    )
    asset_interfaces_description: DmpAssetInterfacesDescription = submodels.planar_interfaces
    control_component_instance: ResourceControlComponentInstance = submodels.planar_control
    capability_description: CapabilityDescription = submodels.planar_capabilities
    asset_interfaces_mapping_configuration: Aimc = submodels.planar_mappings
    variables: Variables = submodels.planar_variables

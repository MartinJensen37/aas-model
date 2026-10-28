"""Resources as the resource ontology ARSO describes them: a production system, a module and a
component of a module.

Each is a ``Resource``. ARSO's **Skills** take the place of the Control Component Instance; the
**Variables** are aas-model's (the live values, and in ``Measurements`` the coordinates). What a kind
of resource does not have is left out (``None``): a component has its Skills only, a production
system its Hierarchical Structures and the coordinates of its own points. What kind of resource an
AAS is, is its asset type: ``.../Resource/System``, ``.../Resource/Module``,
``.../Resource/Component/<Kind>``.
"""

from __future__ import annotations

from typing import Optional

from aas_pydantic.submodel_templates import capability_description as cd
from aas_pydantic.submodel_templates.nameplate import Nameplate

from aas_model.constants import BASE_URL
from aas_model.resource_template.asset import Resource
from aas_model.resource_template.control_component_instance import ResourceControlComponentInstance
from aas_model.resource_template.parameters import ResourceParameters
from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.arso.parameters import Parameters
from aas_model.submodel_templates.variables import Variables

from .submodels import (
    LocatedStructures, ModuleCapabilityDescription, ModuleControlConfiguration, ModuleInterfaces, ModuleSkills,
    lab_nameplate, structure,
)

RESOURCE = f"{BASE_URL}/Resource"


class ArsoResource(Resource):
    """A resource as ARSO describes it: none of ``Resource``'s submodels unless a kind of resource
    has it."""
    nameplate: Optional[Nameplate] = None
    asset_interfaces_description: Optional[DmpAssetInterfacesDescription] = None
    control_component_instance: Optional[ResourceControlComponentInstance] = None     # Skills instead
    capability_description: Optional[cd.CapabilityDescription] = None
    variables: Optional[Variables] = None
    parameters: Optional[ResourceParameters] = None
    asset_interfaces_mapping_configuration: Optional[Aimc] = None


class Module(ArsoResource):
    """A module: the unit of plug and produce, an IEC 61499 program on its own controller.

    It is identified (Nameplate), made of components (Hierarchical Structures), carries out skills
    (Skills), offers the capabilities they realize (Capability Description), is called over OPC UA
    (Asset Interfaces Description and Mapping Configuration) and shows its live values and where it
    is (Variables)."""
    asset_type: str = f"{RESOURCE}/Module"
    nameplate: Nameplate = lab_nameplate()
    hierarchical_structures: LocatedStructures = structure()
    asset_interfaces_description: ModuleInterfaces = ModuleInterfaces(id_short="AssetInterfacesDescription")
    skills: ModuleSkills = ModuleSkills(id_short="Skills")
    variables: Variables = Variables(id_short="Variables")
    asset_interfaces_mapping_configuration: Aimc = Aimc(
        id_short="AssetInterfacesMappingConfiguration", MappingConfigurations=AimcMappingConfigurations(value=[]))
    capability_description: Optional[ModuleCapabilityDescription] = None
    # What was built is the integrator's record, kept outside the AAS (ARSO 0.10).
    control_configuration: Optional[ModuleControlConfiguration] = None
    # A skill's parameters are with the skill; settings of the module itself, when it has any.
    parameters: Optional[Parameters] = None


class Component(ArsoResource):
    """A part of a module that acts (an axis, a pump, a scale): its primitive skills. The module it
    is built into carries them out, so their commands refer to actions of the module's interface
    description. Its asset type ends in its kind (``.../Resource/Component/LinearAxis``)."""
    asset_type: str = f"{RESOURCE}/Component"
    skills: ModuleSkills = ModuleSkills(id_short="Skills")


class ProductionSystem(ArsoResource):
    """A production system (a line): the modules it is made of, each found by its asset id, and the
    coordinates of its own points (where its robots place and pick)."""
    asset_type: str = f"{RESOURCE}/System"
    hierarchical_structures: LocatedStructures = structure()

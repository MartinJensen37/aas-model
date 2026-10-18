"""Generic Resource AAS; operational and domain-specific defaults live in subtypes.

This base declares typed submodels without claiming a physical location,
particular interface, process skill or live observation. Subtypes inherit
only the structure appropriate for their resource kind. A full JSON export
still restores through ``Resource.model_validate_json()``.
"""

from __future__ import annotations

from typing import Any, Optional

from aas_pydantic import AAS

from aas_pydantic.submodel_templates.nameplate import Nameplate
from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures

from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.variables import Variables
from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
from aas_model.constants import BASE_URL

from aas_pydantic.submodel_templates.nameplate import (
    URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    AddressInformation, Street, Zipcode, CityTown, NationalCode,
    OrderCodeOfManufacturer,
)
from aas_model.resource_template.control_component_instance import ResourceControlComponentInstance
from aas_model.resource_template.parameters import ResourceParameters
from aas_model.invocation_authoring import finalize_invocation_addresses


# ═══════════════════════════════════════════════════════════════════════════════
# Submodel field names — documented for reference (model walking replaces old injection)
# ═══════════════════════════════════════════════════════════════════════════════

SUBMODEL_FIELDS = (
    "nameplate", "asset_interfaces_description", "control_component_instance",
    "capability_description", "hierarchical_structures", "variables", "parameters",
    "asset_interfaces_mapping_configuration",
)


# ═══════════════════════════════════════════════════════════════════════════════
# Resource — the shared type model with defaults
# ═══════════════════════════════════════════════════════════════════════════════


class Resource(AAS):
    """Python-authored Resource AAS with shared, independently owned defaults.

    Pass typed submodels to the constructor. Default invocation URL templates
    are resolved during construction, without imposing an invocation policy.
    Standard Pydantic JSON serialization preserves the complete authored
    structure; restoring it does not deep-merge additional resource defaults.
    Use ``aas_model.build_from_model(resource)`` to produce a BaSyx store.

    Resource supplies typed submodels, but does not claim any protocol,
    station skills, telemetry or physical location. Those are inherited by
    the resource types for which they actually apply.
    """

    model_config = {"extra": "forbid"}
    derived_from: str = f"{BASE_URL}/aas/templates/resource"

    # ── Nameplate ─────────────────────────────────────────────────────────
    nameplate: Nameplate = Nameplate(
        id_short="Nameplate",
        URIOfTheProduct=URIOfTheProduct(value="https://smartproductionlab.aau.dk/product/1"),
        ManufacturerName=ManufacturerName(value={"en": "Not specified"}),
        ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Resource"}),
        AddressInformation=AddressInformation(
            Street=Street(value={"en": "Not specified"}),
            Zipcode=Zipcode(value={"en": "Not specified"}),
            CityTown=CityTown(value={"en": "Not specified"}),
            NationalCode=NationalCode(value={"en": "Not specified"}),
        ),
        OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=""),
    )

    # ── Asset Interfaces Description ──────────────────────────────────────
    asset_interfaces_description: DmpAssetInterfacesDescription = DmpAssetInterfacesDescription(
        id_short="AssetInterfacesDescription", InterfaceTemplateForMQTT={},
    )

    # ── Control Component Instance ────────────────────────────────────────
    control_component_instance: ResourceControlComponentInstance = ResourceControlComponentInstance(
        id_short="ControlComponentInstance",
    )

    # ── Capability Description (included unless explicitly omitted) ──────────
    capability_description: Optional[CapabilityDescription] = CapabilityDescription(
        id_short="CapabilityDescription",
    )

    # ── Variables ─────────────────────────────────────────────────────────
    variables: Variables = Variables(id_short="Variables")

    # ── Parameters ────────────────────────────────────────────────────────
    parameters: ResourceParameters = ResourceParameters(
        id_short="Parameters", parameter={},
    )
    # ── Asset Interfaces Mapping Configuration ──────────────────────────────
    asset_interfaces_mapping_configuration: Aimc = Aimc(
        id_short="AssetInterfacesMappingConfiguration",
        MappingConfigurations=AimcMappingConfigurations(value=[]),
    )
    # ── Optional submodels (no defaults — stations opt in) ────────────────
    hierarchical_structures: Optional[HierarchicalStructures] = None

    def model_post_init(self, context: Any) -> None:
        finalize_invocation_addresses(self)



# Existing registration-service consumers import this name.
ResourceTypeAAS = Resource

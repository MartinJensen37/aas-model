"""Resource AAS — Pydantic model for a Resource AAS with type-level defaults.

All Resources must implement certain skills (Halt, Occupy, Release), expose
a StationState property, track PackMLState, and declare a Location.  These
defaults are baked into the Pydantic model so Python-authored instances can
extend them before exporting their complete structure as JSON.

Each submodel's station-agnostic defaults live in its own module under
``resource_template/``:

    nameplate                    — generated IDTA Nameplate + year/country
    asset_interfaces_description — MQTT-extended AID + Halt/Occupy/Release + StationState
    control_component_instance   — extended CCI + Halt/Occupy/Release skills + MQTT endpoint
    capability_description       — IDTA Capability Description for station-authored capabilities
    variables                    — custom Variables + PackMLState/OccupationState
    parameters                   — custom Parameters + Location

This module composes them into ``Resource``. Author instances directly in
Python, export with ``model_dump_json()``, and restore with
``Resource.model_validate_json()``. JSON is an interchange format, not a
separate resource definition language.

Children are named fields or dynamic maps keyed by id_short
(basyx/IDTA-aligned).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from aas_pydantic import AAS

from aas_pydantic.submodel_templates.nameplate import Nameplate
from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures

from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.variables import Variables
from aas_model.submodel_templates import Aimc

from aas_model.resource_template.nameplate import nameplate
from aas_model.resource_template.asset_interfaces_description import asset_interfaces_description
from aas_model.resource_template.asset_interfaces_mapping_configuration import asset_interfaces_mapping_configuration
from aas_model.resource_template.control_component_instance import (
    ResourceControlComponentInstance, control_component_instance,
)
from aas_model.resource_template.capability_description import capability_description
from aas_model.resource_template.variables import variables
from aas_model.resource_template.parameters import ResourceParameters, resource_parameters
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

    Mandatory for all resources:
        - Halt, Occupy, Release actions (MQTT + CCI skills)
        - StationState property
        - PackMLState and OccupationState variables
        - Location parameter
    """

    model_config = {"extra": "forbid"}

    # ── Nameplate ─────────────────────────────────────────────────────────
    nameplate: Nameplate = Field(default_factory=nameplate)

    # ── Asset Interfaces Description ──────────────────────────────────────
    asset_interfaces_description: DmpAssetInterfacesDescription = Field(
        default_factory=asset_interfaces_description,
    )

    # ── Control Component Instance ────────────────────────────────────────
    control_component_instance: ResourceControlComponentInstance = Field(
        default_factory=control_component_instance,
    )

    # ── Capability Description (included unless explicitly omitted) ──────────
    capability_description: Optional[CapabilityDescription] = Field(
        default_factory=capability_description,
    )

    # ── Variables ─────────────────────────────────────────────────────────
    variables: Variables = Field(default_factory=variables)

    # ── Parameters ────────────────────────────────────────────────────────
    parameters: ResourceParameters = Field(default_factory=resource_parameters)
    # ── Asset Interfaces Mapping Configuration ──────────────────────────────
    asset_interfaces_mapping_configuration: Aimc = Field(
        default_factory=asset_interfaces_mapping_configuration,
    )
    # ── Optional submodels (no defaults — stations opt in) ────────────────
    hierarchical_structures: Optional[HierarchicalStructures] = None

    def model_post_init(self, context: Any) -> None:
        finalize_invocation_addresses(self)


# Existing registration-service consumers import this name.
ResourceTypeAAS = Resource

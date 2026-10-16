"""Resource Capability Description, ready for station-specific capabilities."""

from aas_pydantic.submodel_templates.capability_description import CapabilityDescription


def capability_description() -> CapabilityDescription:
    """Start without inventing capability claims or example relationships."""
    return CapabilityDescription(id_short="CapabilityDescription")

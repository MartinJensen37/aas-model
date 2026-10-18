"""Composite-resource template; concrete systems declare their membership."""

from aas_model.constants import CSSX
from aas_model.resource_template.asset import Resource
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures


class CompositeResource(Resource):
    """A composed resource explicitly declares its members in IDTA hierarchy."""

    asset_type: str = f"{CSSX}#CompositeResource"
    hierarchical_structures: HierarchicalStructures

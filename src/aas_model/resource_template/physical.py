"""Physical resources have a configured location, unlike software and systems."""

from aas_model.resource_template.asset import Resource
from aas_model.resource_template.parameters import ResourceParameters


class PhysicalResource(Resource):
    parameters: ResourceParameters = ResourceParameters(id_short="Parameters")


class OperationalResource(PhysicalResource):
    """Operational physical asset, without an assumed native protocol."""

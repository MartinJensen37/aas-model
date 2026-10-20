"""IO-Link (over PROFINET REST) binding: AID's ``iolv_*`` terms are on the
generated form."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForIOLINK_OVER_PROFINET_REST as _BaseInterface, Title,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class DmpIolinkInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()

"""HTTP binding: AID's ``htv_*`` terms are on the generated form; actions use
``htv_methodName`` (WoT default POST), events a ``subprotocol``
(``longpoll``/``sse``)."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForHTTP as _BaseInterface, Title,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class DmpHttpInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()

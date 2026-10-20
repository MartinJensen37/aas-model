"""Modbus binding: AID's ``modv_*`` terms are on the generated form and the
endpoint metadata (byte and word order)."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForMODBUS as _BaseInterface, Title,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class DmpModbusInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()

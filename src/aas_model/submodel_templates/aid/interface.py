"""What every interface shares: its endpoint metadata."""

from __future__ import annotations

from typing import Optional, Union

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, ContentType_for_content_type_2, EndpointMetadata, security_t, securityDefinitions,
    securityDefinitions_t,
)


class DmpEndpointMetadata(EndpointMetadata):
    """The AID EndpointMetadata with its mandatory children present: ``base``
    and ``contentType`` to be filled in, an empty ``security`` selection and
    ``securityDefinitions``."""
    base: Optional[Base] = Base()
    contentType: Optional[Union[ContentType, ContentType_for_content_type_2]] = ContentType()
    security: security_t = security_t()
    securityDefinitions: securityDefinitions_t = securityDefinitions()

"""Finalize the invocation addresses of a Resource's Operations while authoring it."""

from __future__ import annotations

import base64
from urllib.parse import quote

from aas_model.constants import BASE_URL

OPERATION_PATH = "{operation_path}"


def operation_path(submodel_id: str, id_short_path: str) -> str:
    """The path an Operation is invoked at in the AAS API:
    ``/submodels/{base64url(submodel id)}/submodel-elements/{idShortPath}/invoke``.

    A submodel id is globally unique and an idShortPath unique within its submodel, so no two Operations share
    a path. The DMP serves exactly this path and rejects any other.
    """
    encoded = base64.urlsafe_b64encode(submodel_id.encode("utf-8")).decode("ascii").rstrip("=")
    return f"/submodels/{encoded}/submodel-elements/{quote(id_short_path, safe='.')}/invoke"


def finalize_invocation_addresses(asset) -> None:
    """Fill the ``{operation_path}`` of each skill Operation's invocationDelegation qualifier.

    The ids are those the id injector will assign (``{aas_id}/submodels/{idShort}``), unless authored.
    Explicit concrete invocation URLs are authored data and are left intact.
    Call again after adding template-based skills to an existing instance.
    """
    cci = asset.control_component_instance
    if cci is None or cci.Skills is None:
        return

    aas_id = asset.id if asset.id and asset.id != asset.id_short else f"{BASE_URL}/aas/{asset.id_short}"
    submodel_id = cci.id if cci.id and cci.id != cci.id_short else f"{aas_id}/submodels/{cci.id_short}"
    for skill_key, skill in (cci.Skills.Skill or {}).items():
        operation = skill.operation
        if operation is None:
            continue
        path = operation_path(submodel_id, f"{cci.Skills.id_short}.{skill_key}.{operation.id_short}")
        for qualifier in operation.qualifiers:
            if qualifier.type_ == "invocationDelegation":
                qualifier.value = qualifier.value.replace(OPERATION_PATH, path)

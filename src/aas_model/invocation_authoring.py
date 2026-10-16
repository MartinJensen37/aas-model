"""Finalize shared invocation addresses while authoring a Resource AAS."""

from __future__ import annotations

from urllib.parse import quote_plus


def _encode_segment(value: str) -> str:
    # Match Java URLEncoder for UTF-8 path segments, except spaces are %20.
    return quote_plus(value, safe="*").replace("+", "%20").replace("~", "%7E")


def finalize_invocation_addresses(asset) -> None:
    """Fill existing invocation qualifier templates while authoring a Resource.

    Explicit concrete invocation URLs are authored data and are left intact.
    Call again after adding template-based skills to an existing instance.
    """
    cci = asset.control_component_instance
    if cci is None or cci.Skills is None:
        return

    for skill_key, skill in (cci.Skills.Skill or {}).items():
        operation = skill.operation
        if operation is None:
            continue
        for qualifier in operation.qualifiers:
            if qualifier.type_ == "invocationDelegation":
                qualifier.value = qualifier.value.replace(
                    "{aas_id_short}", _encode_segment(asset.id_short)
                ).replace("{skill}", _encode_segment(skill_key))

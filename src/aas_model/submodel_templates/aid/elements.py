"""Building blocks shared by the AID extension modules."""

from __future__ import annotations

from typing import ClassVar, List

from pydantic import model_validator

from aas_pydantic import Property, SubmodelElementList


class StringList(SubmodelElementList):
    """A list of string Properties (``op``, ``required``): build it from the
    values, ``StringList(value=[Property(value="a"), …])``. Each member gets an
    idShort for the conversion — the value itself when it is a valid idShort,
    else ``value_<i>`` — which AASd-120 drops on the wire, and its value as
    ``displayName`` (which list members may carry), so a viewer shows the
    names. An authored display name is kept; a value over 128 characters (the
    MultiLanguageNameType limit) gets none rather than a truncated one."""
    item_type: ClassVar = Property
    value: List[Property] = []

    @model_validator(mode="after")
    def _member_id_shorts(self):
        seen = set()
        for index, member in enumerate(self.value):
            text = str(member.value)
            short = text if text[:1].isalpha() and all(c.isalnum() or c == "_" for c in text) else f"value_{index}"
            while short in seen:
                short = f"{short}_{index}"
            seen.add(short)
            member.id_short = short
            if not member.display_name and 0 < len(text) <= 128:
                member.display_name = {"en": text}
        return self

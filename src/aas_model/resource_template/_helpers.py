"""Keep generated submodel container keys and element idShorts aligned."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aas_pydantic import SubmodelElement


def put(container: Any, key: str, element: SubmodelElement) -> SubmodelElement:
    """Assign *element* into *container* under *key*, stamping its id_short
    from the key.

    *container* is a values model (``setattr`` onto an existing field) or a
    dynamic ``Dict[str, X]`` map (``container[key] = ...``).  The key is the
    single source of truth for the id_short.
    """
    element.id_short = key
    if isinstance(container, BaseModel):
        setattr(container, key, element)
    else:
        container[key] = element
    return element

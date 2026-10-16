"""Generated aas_pydantic models from IDTA submodel templates.

Usage::

    from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
    from aas_pydantic.submodel_templates.nameplate import Nameplate
    from aas_pydantic.submodel_templates.time_series import TimeSeries

Regenerate::

    python scripts/idta_generate.py

The default command writes the pinned templates to this package. To
generate one template, pass its path relative to
``submodel-templates/published/``. Each generated module records its source
template path in its module docstring. Containers use direct fields preserving
idShort casing; cardinality controls required, optional, and dynamic-map fields,
while SubmodelElementLists retain list semantics.
"""

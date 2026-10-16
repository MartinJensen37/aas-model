"""Concrete Resource definitions, with one Python module per resource.

Shared defaults belong in ``resource_template``; station-specific authoring
belongs here, for example in ``stopperingModule.py``. Each factory returns a
fresh Resource that supports the same JSON and AAS build APIs::

    from aas_model import Resource, build_from_model
    from aas_model.resource_instances.stopperingModule import syntegon_stoppering

    resource = syntegon_stoppering()
    config_json = resource.model_dump_json(indent=2)
    restored = Resource.model_validate_json(config_json)
    store = build_from_model(restored)
"""

from .stopperingModule import syntegon_stoppering

__all__ = ["syntegon_stoppering"]

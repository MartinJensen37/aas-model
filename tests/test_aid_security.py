"""AID 1.1 §2.24-2.25: every interface selects a security scheme; without
security it references its own ``nosec_sc``. Secrets never live in the AID."""

from __future__ import annotations

import pytest

from aas_model.id_injector import inject_ids
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.testing import build_aid, http_interface, mqtt_interface


def _interfaces(aid):
    for family in type(aid).model_fields:
        if family.startswith("InterfaceTemplateFor"):
            yield from (getattr(aid, family) or {}).items()


def _assert_nosec(aid):
    for key, interface in _interfaces(aid):
        metadata = interface.EndpointMetadata
        assert metadata.securityDefinitions.nosec_sc is not None, key
        assert metadata.securityDefinitions.nosec_sc.scheme.value == "nosec"
        [reference] = metadata.security.value
        keys = [k.value for k in reference.value.key]
        assert keys == [aid.id, key, "EndpointMetadata", "securityDefinitions", "nosec_sc"]


@pytest.mark.parametrize("name", sorted(RESOURCE_FACTORIES))
def test_every_published_interface_references_its_own_nosec_scheme(name):
    resource = RESOURCE_FACTORIES[name]().model_copy(deep=True)
    inject_ids(resource)
    _assert_nosec(resource.asset_interfaces_description)


def test_a_selected_scheme_is_kept_and_selection_is_idempotent():
    aid = build_aid(http=http_interface("http://device:8080/"), mqtt=mqtt_interface("mqtt://broker:1883/"))
    aid.id = "a/submodels/AID"
    aid.select_nosec()
    aid.select_nosec()
    _assert_nosec(aid)

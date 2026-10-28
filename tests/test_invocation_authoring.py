import base64

import pytest
from pydantic import ValidationError

from aas_model import Resource, build_from_model
from aas_model.invocation_authoring import finalize_invocation_addresses, operation_path
from aas_model.resource_template import MQTT_INTERFACE, MqttOperationalStation as Station, extended_skill
from aas_model.testing import aimc_mapping


def _delegation(skill):
    return next(q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation").value


def _b64(identifier: str) -> str:
    return base64.urlsafe_b64encode(identifier.encode()).decode().rstrip("=")


def test_an_operation_is_invoked_at_its_aas_api_path():
    assert operation_path("urn:x/sm", "Skills.Halt.operation") == \
        f"/submodels/{_b64('urn:x/sm')}/submodel-elements/Skills.Halt.operation/invoke"
    assert operation_path("urn:x/sm", "List[0].operation").endswith("/List%5B0%5D.operation/invoke")


def test_default_skills_are_delegated_to_the_path_of_their_built_operation():
    asset = Station(id_short="LineA")
    built = {o.id_short: o for o in build_from_model(asset)}["ControlComponentInstance"]
    for skill_name, skill in asset.control_component_instance.Skills.Skill.items():
        assert _delegation(skill) == \
            f"http://dmp:8080/submodels/{_b64(built.id)}/submodel-elements/Skills.{skill_name}.operation/invoke"


def test_an_authored_aas_id_is_the_base_of_the_submodel_id():
    asset = Station(id_short="LineA", id="urn:plant:line-a")
    finalize_invocation_addresses(asset)
    halt = asset.control_component_instance.Skills.Skill["Halt"]
    assert _b64("urn:plant:line-a/submodels/ControlComponentInstance") in _delegation(halt)


def test_skills_added_later_are_finalized_on_request():
    asset = Station(id_short="LineA")
    skill = extended_skill("Weigh", MQTT_INTERFACE)
    asset.control_component_instance.Skills.Skill["Weigh"] = skill
    finalize_invocation_addresses(asset)
    assert _delegation(skill).endswith("/submodel-elements/Skills.Weigh.operation/invoke")


def test_resource_authoring_does_not_accept_per_resource_origin():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Resource(id_short="Station", delegation_base="http://old:8080")


def test_finalizer_preserves_concrete_authored_invocation_urls():
    asset = Station(id_short="Station")
    qualifier = asset.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0]
    qualifier.value = "http://dmp-station:8080/custom/Halt"
    finalize_invocation_addresses(asset)

    assert qualifier.value == "http://dmp-station:8080/custom/Halt"


@pytest.mark.parametrize("url", [
    "http://dmp-station:8080/custom/Halt",
    "https://example.test/custom/invocation",
])
def test_pydantic_dict_and_json_import_preserve_authored_invocation_urls(url):
    asset = Station(id_short="Station")
    asset.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0].value = url

    from_dict = Resource.model_validate(asset.model_dump(mode="json"))
    from_json = Resource.model_validate_json(asset.model_dump_json())

    for restored in (from_dict, from_json):
        assert restored.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0].value == url


def test_an_invocation_timeout_is_a_positive_duration_of_at_most_fifteen_minutes():
    mapping = aimc_mapping(sources=[], sinks=[], invocation_timeout="PT2M")
    assert mapping.InvocationTimeout.value == "PT2M"
    assert mapping.InvocationTimeout.semantic_id == "https://smartproductionlab.aau.dk/aimc/InvocationTimeout/1/0"
    for invalid in ("PT0S", "PT16M", "PT1.5S", "30", "P1D"):
        with pytest.raises(ValidationError):
            aimc_mapping(sources=[], sinks=[], invocation_timeout=invalid)

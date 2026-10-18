import pytest
from pydantic import ValidationError

from aas_model import Resource
from aas_model.invocation_authoring import finalize_invocation_addresses
from aas_model.resource_template import MqttOperationalStation as Station, extended_skill


def test_default_invocation_qualifiers_use_fixed_origin_and_encoded_segments():
    asset = Resource(id_short="Cell A/ß")
    skill = extended_skill("Skill *~/A")
    asset.control_component_instance.Skills.Skill["Skill *~/A"] = skill

    finalize_invocation_addresses(asset)

    qualifier = next(
        q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation"
    )
    assert qualifier.value == (
        "http://dmp:8080/operations/Cell%20A%2F%C3%9F/Skill%20*%7E%2FA"
    )


def test_default_skills_share_origin_and_keep_exact_owner_and_skill_names():
    asset = Station(id_short="Line A")
    for skill_name, skill in asset.control_component_instance.Skills.Skill.items():
        qualifier = next(
            q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation"
        )
        assert qualifier.value == f"http://dmp:8080/operations/Line%20A/{skill_name}"


def test_resource_authoring_does_not_accept_per_resource_origin():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        Resource(id_short="Station", delegation_base="http://old:8080")

    exported = Station(id_short="Cell A").model_dump(mode="json")
    qualifiers = exported["control_component_instance"]["Skills"]["Skill"]["Halt"]["operation"]["qualifiers"]
    delegation = next(q for q in qualifiers if q["type_"] == "invocationDelegation")
    assert delegation["value"] == "http://dmp:8080/operations/Cell%20A/Halt"


def test_finalizer_preserves_concrete_authored_invocation_urls():
    asset = Station(id_short="Station")
    qualifier = asset.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0]
    qualifier.value = "http://dmp-station:8080/operations/Station/Halt"
    finalize_invocation_addresses(asset)

    assert qualifier.value == "http://dmp-station:8080/operations/Station/Halt"


@pytest.mark.parametrize("url", [
    "http://dmp-station:8080/operations/Station/Halt",
    "https://example.test/custom/invocation",
])
def test_pydantic_dict_and_json_import_preserve_authored_invocation_urls(url):
    asset = Station(id_short="Station")
    asset.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0].value = url

    from_dict = Resource.model_validate(asset.model_dump(mode="json"))
    from_json = Resource.model_validate_json(asset.model_dump_json())

    for restored in (from_dict, from_json):
        assert restored.control_component_instance.Skills.Skill["Halt"].operation.qualifiers[0].value == url

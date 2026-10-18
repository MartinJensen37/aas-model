"""Focused validation for handwritten MQTT and OPC UA AID subclasses."""

import pytest
from pydantic import ValidationError

from aas_model.submodel_templates.aid import (
    MqttActionForm,
    OpcuaAction,
    OpcuaActionForm,
    UavComponentOf,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    HtvMethodName,
    MqvQos,
    UavBrowsePath,
)


def test_mqtt_action_form_rejects_http_binding_fields():
    with pytest.raises(ValidationError, match="htv_methodName"):
        MqttActionForm(htv_methodName=HtvMethodName(value="POST"))


def test_opcua_action_form_rejects_mqtt_binding_fields():
    with pytest.raises(ValidationError, match="mqv_qos"):
        OpcuaActionForm(mqv_qos=MqvQos(value="1"))

    assert OpcuaActionForm(uav_browsePath=UavBrowsePath(value="Objects/Method"))


@pytest.mark.parametrize("component", [None, UavComponentOf(), UavComponentOf(value="  ")])
def test_opcua_action_requires_nonempty_component_of(component):
    with pytest.raises(ValidationError, match="non-empty uav_componentOf"):
        OpcuaAction(uav_componentOf=component)


def test_opcua_action_accepts_component_of_node_id():
    action = OpcuaAction(uav_componentOf=UavComponentOf(value="ns=1;s=Controller"))

    assert action.uav_componentOf.value == "ns=1;s=Controller"

"""Reusable typed defaults for operational resources, per native protocol."""

from .submodels import (
    PACKML_SKILLS, INVOKE_ONLY_SKILLS, OPCUA_STATION, OperationalVariables,
    action_member_ref, command_reply,
    MqttInterfaces, OperationalMqttInterfaces, OperationalMqttControlComponent, OperationalMqttMappings,
    OpcuaInterfaces, OperationalOpcuaInterfaces, OperationalOpcuaControlComponent, OperationalOpcuaMappings,
)

__all__ = [
    "PACKML_SKILLS", "INVOKE_ONLY_SKILLS", "OPCUA_STATION", "OperationalVariables",
    "action_member_ref", "command_reply",
    "MqttInterfaces", "OperationalMqttInterfaces", "OperationalMqttControlComponent", "OperationalMqttMappings",
    "OpcuaInterfaces", "OperationalOpcuaInterfaces", "OperationalOpcuaControlComponent", "OperationalOpcuaMappings",
]

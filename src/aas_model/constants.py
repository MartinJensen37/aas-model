"""
Shared constants for the templates package.

All project-specific semantic IDs are defined here.
IDTA-defined semantic IDs (admin-shell.io/idta/...) stay in their generated templates.
Third-party semantic IDs (w3.org, schema.org, purl.org, etc.) stay inline in their modules.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Base URLs
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://smartproductionlab.aau.dk"
SCHEMA_BASE = "https://aausmartproductionlab.github.io/AP2030-UNS/MQTTSchemas"

# ═══════════════════════════════════════════════════════════════════════════════
# Infrastructure defaults
# ═══════════════════════════════════════════════════════════════════════════════

BROKER = "mqtt://192.168.0.104:1883"
SITE = "NN/Nybrovej/InnoLab"

# Shared invocation service origin. Resource-specific identity belongs in
# authored URL path segments, never in a per-resource host/config setting.
INVOCATION_ORIGIN = "http://dmp:8080"

# ═══════════════════════════════════════════════════════════════════════════════
# Ontology
# ═══════════════════════════════════════════════════════════════════════════════

CSSX = "http://www.w3id.org/aau-ra/cssx"

# ═══════════════════════════════════════════════════════════════════════════════
# MQTT Asset Interfaces Description — extended fields
# ═══════════════════════════════════════════════════════════════════════════════

AID_MQTT_RESPONSE_FORM = f"{BASE_URL}/aid/MqttResponseForm/1/0"
AID_MQTT_RETAIN = f"{BASE_URL}/aid/MqttRetain/1/0"
AID_MQTT_CONTROL_PACKET = f"{BASE_URL}/aid/MqttControlPacket/1/0"
AID_MQTT_QOS = f"{BASE_URL}/aid/MqttQos/1/0"
# WoT MQTT binding (MQTT 5) request/reply correlation: ``requestReply``
# marks the action as a correlated request/reply interaction and
# ``responseTopic`` names the MQTT 5 Response Topic the reply is
# delivered on (the requester sets it as the PUBLISH response-topic
# property; the responder echoes the request's Correlation Data).
AID_MQTT_REQUEST_REPLY = f"{BASE_URL}/aid/MqttRequestReply/1/0"
AID_MQTT_RESPONSE_TOPIC = f"{BASE_URL}/aid/MqttResponseTopic/1/0"
AID_INPUT_SCHEMA = f"{BASE_URL}/aid/InputSchema/1/0"
AID_OUTPUT_SCHEMA = f"{BASE_URL}/aid/OutputSchema/1/0"
AID_SYNCHRONOUS = "https://www.w3.org/2019/wot/td#synchronous"
AID_WOT_SAFE = "https://www.w3.org/2019/wot/td#safe"
AID_WOT_IDEMPOTENT = "https://www.w3.org/2019/wot/td#idempotent"

# WoT Thing Description 2.0 ``ActionAffordance.input`` / ``.output`` vocabulary
# (w3.org — kept inline per the constants policy).  Shared by the MQTT and the
# generic (Dmp) action DataSchemas.
AID_ACTION_INPUT = "https://www.w3.org/2019/wot/td#hasInput"
# WoT TD 1.1 §5.3.1.5 EventAffordance: ``subscription`` (payload of the
# subscribe request), ``data`` (each notification), ``dataResponse`` (the
# consumer's answer to a notification), ``cancellation`` (payload of the
# unsubscribe request). TD 2.0 (Working Draft) keeps the same terms.
AID_EVENT_SUBSCRIPTION = "https://www.w3.org/2019/wot/td#hasSubscriptionSchema"
AID_EVENT_DATA = "https://www.w3.org/2019/wot/td#hasNotificationSchema"
AID_EVENT_DATA_RESPONSE = "https://www.w3.org/2019/wot/td#hasNotificationResponseSchema"
AID_EVENT_CANCELLATION = "https://www.w3.org/2019/wot/td#hasCancellationSchema"
AID_EVENT_AFFORDANCE = "https://www.w3.org/2019/wot/td#EventAffordance"

# OPC UA events. OPC 10101 (WoT Binding for OPC UA, v1.00) defines no event
# vocabulary, so these terms live in this project's namespace: the EventType a
# subscription is filtered to (where clause, OfType) and, per data-schema
# property, the field's browse path relative to the event (select clause).
AID_OPCUA_EVENT_TYPE = f"{BASE_URL}/aid/OpcuaEventType/1/0"
AID_OPCUA_EVENT_FIELD = f"{BASE_URL}/aid/OpcuaEventField/1/0"
AID_ACTION_OUTPUT = "https://www.w3.org/2019/wot/td#hasOutput"
AID_WOT_OPERATION_TYPE = "https://www.w3.org/2019/wot/td#hasOperationType"
AID_WOT_RESPONSE_FORM = "https://www.w3.org/2019/wot/hypermedia#response"

# ═══════════════════════════════════════════════════════════════════════════════
# AIMC — DMP extensions of the IDTA MappingConfiguration
# ═══════════════════════════════════════════════════════════════════════════════
# IDTA AIMC 2.0 defines Sources, Sinks, Transformation and DefaultPollingInterval.
# Everything an operation mapping adds lives in this project's namespace, so a
# standard AIMC consumer can tell the additions apart (DMP PLAN P3). Per
# invocation: command (IDTA Sources/Transformation/Sinks) → optional status
# phase (Status*) → response phase (Response*).

# Status phase: status properties/events of the action's AID, the Lua that
# decides "running"/"done"/"failed", and how long to wait for it (seconds).
AIMC_STATUS_SOURCES = f"{BASE_URL}/aimc/StatusSources/1/0"
AIMC_STATUS_SOURCE = f"{BASE_URL}/aimc/StatusSource/1/0"
AIMC_STATUS_SOURCE_REFERENCE = f"{BASE_URL}/aimc/StatusSource/Source/1/0"
AIMC_STATUS_SOURCE_ID = f"{BASE_URL}/aimc/StatusSource/SourceId/1/0"
AIMC_STATUS_TRANSFORMATION = f"{BASE_URL}/aimc/StatusTransformation/1/0"
AIMC_STATUS_TIMEOUT = f"{BASE_URL}/aimc/StatusTimeout/1/0"

# Response phase: the elements read once after the command (or status phase),
# the Lua that builds the caller's reply, and the elements it writes.
AIMC_RESPONSE_SOURCES = f"{BASE_URL}/aimc/ResponseSources/1/0"
AIMC_RESPONSE_SOURCE = f"{BASE_URL}/aimc/ResponseSource/1/0"
AIMC_RESPONSE_SOURCE_REFERENCE = f"{BASE_URL}/aimc/ResponseSource/Source/1/0"
AIMC_RESPONSE_SOURCE_ID = f"{BASE_URL}/aimc/ResponseSource/SourceId/1/0"
AIMC_RESPONSE_TRANSFORMATION = f"{BASE_URL}/aimc/ResponseTransformation/1/0"
AIMC_RESPONSE_SINKS = f"{BASE_URL}/aimc/ResponseSinks/1/0"
AIMC_RESPONSE_SINK = f"{BASE_URL}/aimc/ResponseSink/1/0"
AIMC_RESPONSE_SINK_REFERENCE = f"{BASE_URL}/aimc/ResponseSink/Sink/1/0"
AIMC_RESPONSE_SINK_ID = f"{BASE_URL}/aimc/ResponseSink/SinkId/1/0"

# Which source updates execute an ordinary mapping.
AIMC_EXECUTION_SEMANTICS = f"{BASE_URL}/aimc/ExecutionSemantics/1/0"
AIMC_TRIGGER_SOURCE_IDS = f"{BASE_URL}/aimc/ExecutionSemantics/TriggerSourceIds/1/0"

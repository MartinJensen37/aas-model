# AID extension: actions, events and the terms AID leaves EXTERNAL

Status: draft, 2026-10-17. Code: `src/aas_model/submodel_templates/aid.py`.
Consumer: `aas-camel-dmp` (SPEC §5.2).

## 1. Rules

1. **AID 1.2 is normative for everything it defines**: element idShorts,
   semantic IDs, cardinalities and the `base`/`href` rules of Annex B. The
   extension never redefines an AID element or adds a second element for the
   same meaning. If the extension and AID disagree, the extension is wrong.
2. **No EXTERNAL.** AID Annex D marks some WoT TD terms "EXTERNAL", meaning
   they live in a separate Thing Description referenced through
   `ExternalDescriptor`. We don't do that, because it would mean maintaining
   two overlapping descriptions. A term we need is added *inside* the AID. A
   term we don't need is left out and listed in §2 with the reason.
3. **Semantic IDs come from the owner of the term.** WoT TD terms use the
   W3C IRIs of the TD 1.1 context (`td:`, `hctl:`, `jsonschema:`), binding
   terms use the IRIs of their binding (W3C, OPC 10101). Only terms that no
   specification defines get an ID under
   `https://smartproductionlab.aau.dk/aid/<Name>/1/0`.
4. **Where AID says nothing, the WoT protocol bindings apply**: operation
   defaults, actions, events. Where a WoT draft contradicts something AID
   defines, AID wins. Examples: the MQTT topic stays in `href`, not in the
   newer `mqv:topic`; `modv_zeroBasedAddressing` stays usable although the
   WoT Modbus draft deprecates it; BACnet keeps AID's idShort
   `bacv_useService`.
5. **Defaults are not authored.** The TD defaults apply when a term is
   absent. A builder writes a term only to state something the default
   doesn't say.

## 2. WoT TD terms that AID 1.2 does not carry

| TD term | AID 1.2 | Decision | idShort, semantic ID |
| --- | --- | --- | --- |
| `actions` (members) | Container only (`td#ActionAffordance`), no member structure | **Add** (§3.2) | member: `…/aid/ActionDefinition/1/0`, supplemental `td#name` |
| `events` (members) | Container only (`td#EventAffordance`) | **Add** (§3.3) | member: `…/aid/EventDefinition/1/0`, supplemental `td#name` |
| Form `op` | EXTERNAL | **Add** (§3.4), optional | `op`, `hctl#hasOperationType` |
| Form `response` | Not mentioned | **Add**, actions only | `response`, `hctl#returns` |
| `readOnly`, `writeOnly` | EXTERNAL | **Add** on properties | `readOnly`/`writeOnly`, `json-schema#readOnly`/`#writeOnly` |
| `titles`, `descriptions` | EXTERNAL | Not added: AAS `displayName`/`description` are multi-language already | — |
| `links`, `profile` | EXTERNAL | Not added: no consumer | — |
| `schemaDefinitions`, `additionalResponses` | EXTERNAL / not mentioned | Not added: only needed together, no consumer | — |
| `contentCoding`, `scopes` | Not mentioned | Not added: no consumer | — |
| `required`, `format`, `pattern`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`, `oneOf`, `contentEncoding`, `contentMediaType` | EXTERNAL | Not added yet. A consumer that needs one adds it under rule 3 | — |

`uriVariables` is defined by AID on properties. The extension reuses the same
element (`td#hasUriTemplateSchema`) on actions and events.

## 3. Additions

### 3.1 Property affordance

A property stays the AID `PropertyDefinition` with its AID form. Added:

| idShort | Type | Semantic ID | Card. | Meaning |
| --- | --- | --- | --- | --- |
| `readOnly` | Property xs:boolean | `https://www.w3.org/2019/wot/json-schema#readOnly` | 0..1 | Not writable. Default false. |
| `writeOnly` | Property xs:boolean | `https://www.w3.org/2019/wot/json-schema#writeOnly` | 0..1 | Not readable. Default false. |

`observable` (AID, `td#isObservable`) is how AID says that a property can be
observed. A consumer that finds no `op` derives the operations from these
three flags (§3.4).

### 3.2 Action affordance (`actions/{name}`)

| idShort | Type | Semantic ID | Card. | Meaning |
| --- | --- | --- | --- | --- |
| *(the SMC)* | SMC | `…/aid/ActionDefinition/1/0`, suppl. `https://www.w3.org/2019/wot/td#name` | | One action. The idShort is the action name. |
| `title` | AID `Title` | AID | 0..1 | |
| `input` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasInputSchema` | 0..1 | Request payload |
| `output` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasOutputSchema` | 0..1 | Result payload |
| `safe` | Property xs:boolean | `https://www.w3.org/2019/wot/td#isSafe` | 0..1 | Changes no state. Default false. |
| `idempotent` | Property xs:boolean | `https://www.w3.org/2019/wot/td#isIdempotent` | 0..1 | Repeatable with the same result. Default false. |
| `synchronous` | Property xs:boolean | `https://www.w3.org/2019/wot/td#isSynchronous` | 0..1 | The result arrives in the reply to the invocation. Absent: unknown. |
| `uriVariables` | AID `uriVariables` | AID | 0..1 | |
| `forms` | Form (§3.4) | AID | 1 | |

A DataSchema SMC is AID's own data schema (`type`, `title`, `enum`, `const`,
`default`, `unit`, `min_max`, `lengthRange`, `items`, `itemsRange`,
`properties`, …), the same structure as a property. Its description is the
AAS `description`.

### 3.3 Event affordance (`events/{name}`)

| idShort | Type | Semantic ID | Card. | Meaning |
| --- | --- | --- | --- | --- |
| *(the SMC)* | SMC | `…/aid/EventDefinition/1/0`, suppl. `https://www.w3.org/2019/wot/td#name` | | One event |
| `title` | AID `Title` | AID | 0..1 | |
| `subscription` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasSubscriptionSchema` | 0..1 | Payload sent when subscribing |
| `data` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasNotificationSchema` | 0..1 | Payload of each notification |
| `dataResponse` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasNotificationResponseSchema` | 0..1 | The consumer's answer to a notification |
| `cancellation` | DataSchema SMC | `https://www.w3.org/2019/wot/td#hasCancellationSchema` | 0..1 | Payload sent when unsubscribing |
| `uriVariables` | AID `uriVariables` | AID | 0..1 | |
| `forms` | Form (§3.4) | AID | 1 | |

An event has no current value. A consumer sees only notifications sent while
it is subscribed.

### 3.4 Form additions

The AID form already carries every binding term of every protocol. The
extension adds:

| idShort | Type | Semantic ID | Card. | Meaning |
| --- | --- | --- | --- | --- |
| `op` | SML of Property xs:string | `https://www.w3.org/2019/wot/hypermedia#hasOperationType` | 0..1 | The WoT operations this form serves. It only narrows the defaults below. |
| `response` | SMC | `https://www.w3.org/2019/wot/hypermedia#returns` | 0..1 | WoT ExpectedResponse, on action forms only. One child: `contentType` (AID `ContentType`). Absent: the form's `contentType`. |

Default operations when `op` is absent (TD 1.1, with AID's `observable`):

| Affordance | Operations |
| --- | --- |
| Property | `readproperty` unless `writeOnly`; `writeproperty` unless `readOnly`; `observeproperty` and `unobserveproperty` if `observable` |
| Action | `invokeaction` |
| Event | `subscribeevent`, `unsubscribeevent` |

`queryaction` and `cancelaction` are WoT asynchronous actions. No binding
used here defines them, and the DMP doesn't support them.

### 3.5 Terms no specification defines

| idShort | Where | Semantic ID | Meaning |
| --- | --- | --- | --- |
| `mqv_responseTopic` | MQTT action form | `…/aid/MqttResponseTopic/1/0` | MQTT 5 request/reply: the topic the device publishes the result to. The request carries it as Response Topic plus Correlation Data, and the reply echoes the Correlation Data. Present = request/reply. |
| `uav_componentOf` | OPC UA action (affordance) | `http://opcfoundation.org/UA/WoT-Binding/componentOf` (OPC 10101 §7.1.3) | NodeId of the Object that owns the Method. Mandatory on OPC UA actions. |
| `uav_eventType` | OPC UA event (affordance) | `…/aid/OpcuaEventType/1/0` | EventType filter (OfType, subtypes included) |
| `uav_eventField` | Member of an OPC UA event's `data` | `…/aid/OpcuaEventField/1/0` | Browse path of the event field relative to the event. Absent: the member name in namespace 0. |

The `mqv_`/`uav_` prefixes follow AID's convention of one prefix per
protocol. The DMP semantic IDs distinguish these terms from W3C/OPC terms.

## 4. Actions and events per protocol

| Protocol | Action form | Event form | Source |
| --- | --- | --- | --- |
| HTTP | `htv_methodName` (AID, card. 1; WoT default POST). The response body is `output`, and `response.contentType` defaults to the form's. | `htv_methodName` GET plus `subprotocol` `longpoll` or `sse` | WoT HTTP binding, AID 2.24.1 |
| MQTT | `href` = request topic (AID B.2: relative to base, `.//` for a leading `/`, `%23` for `#`). `mqv_controlPacket` defaults to `publish`. `mqv_qos`/`mqv_retain` as in AID. `mqv_responseTopic` (§3.5) for a result. | `href` = topic or filter. `mqv_controlPacket` defaults to `subscribe`. | WoT MQTT binding defaults (consumer view, matching AID's "in relation to the broker") |
| OPC UA | `href` `/?id=<Method NodeId>`, `uav_componentOf` on the action. Input and output are the Method's arguments (object members by argument name). Service: Call. | `href` (or `uav_browsePath`) = event notifier, `uav_eventType`, `data` fields with `uav_eventField`. Event monitored item. | OPC 10101; events are our addition |
| Modbus | WoT default `writeSingleCoil` (`modv_function`/`modv_entity` as in AID). Modelable, but a write reports no result, so the DMP doesn't invoke it (PLAN A6). | None: the binding defines no events | WoT Modbus binding |
| BACnet | `bacv_useService` (`GetEventInfo`, `AcknowledgeAlarm`), `uriVariables` such as `commandPriority` | `subscribeevent` (COV / event notification) | WoT BACnet binding. Not supported by the DMP. |
| IO-Link, SNMP, CAN | Not modelled | Not modelled | AID defines properties only |

## 5. Corrections to the current extension

Each of these redefines or contradicts AID or W3C:

1. `MqttForm.mqv_control_packet` (our ID) duplicates AID's
   `mqv_controlPacket`, which the generated form already has. `mqv_retain`
   and `mqv_qos` are redeclared with our IDs and made mandatory. **Remove
   all three and use AID's optional terms.** The builders author the
   device's view (`publish` on properties, `subscribe` on actions), the
   inverse of AID/WoT. They stop authoring the packet; the defaults are
   correct.
2. `MqttResponseForm` adds `href`, `mqv_retain` and `mqv_control_packet` to
   the WoT ExpectedResponse, and `mqv_request_reply` duplicates "a response
   topic is present". **Keep one term: `mqv_responseTopic`.**
   `orchestrator.py` and `production_planner.py` attach invented W3C IRIs
   (`mqtt#requestReply`, `mqtt#responseTopic`). `synchronous` appears with
   an `apex` ID.
3. Wrong W3C IRIs in `constants.py`: `td#safe` → `td#isSafe`,
   `td#idempotent` → `td#isIdempotent`, `td#synchronous` →
   `td#isSynchronous`, `td#hasInput`/`td#hasOutput` →
   `td#hasInputSchema`/`td#hasOutputSchema`, `td#hasOperationType` →
   `hypermedia#hasOperationType`, `hypermedia#response` →
   `hypermedia#returns`.
4. Action and event members carry the *container's* semantic ID
   (`td#ActionAffordance`). AID gives property members their own ID
   (`PropertyDefinition`) and puts the TD class on the container. **Mirror
   that** (§3.2, §3.3).
5. `ModbusEndpointMetadata` adds `modv_pollingTime`, `modv_timeout` and
   `modv_type`. AID allows only the byte and word order there, and the
   generated EndpointMetadata already has them. **Remove.**
6. `BacnetForm` puts `bacv_isISO8601`, `bacv_hasBinaryRepresentation`,
   `bacv_hasFieldName` and `bacv_hasContextTag` directly on the form. AID
   nests them in `bacv_hasDataType`, which the generated form already has.
   **Remove.**
7. `ModbusForm`, `BacnetForm`, `IolinkForm` and `OpcuaForm` redeclare terms
   the generated form already has. With `op` and `response` on one shared
   form, the protocol-specific form, property and interaction-metadata
   classes go away. Only MQTT actions (`mqv_responseTopic`) and OPC UA
   actions and events (`uav_*`) keep a subclass.
8. `op` is a mandatory single Property. TD allows several operations and a
   default when absent. **Optional SML** (§3.4).
9. `OpcuaForm` documents `uav_browsePath` as root-relative. AID: "an
   absolute path … starting from the root node" (`/Root/Objects/…`).
10. `DmpForm` makes the form's `security` mandatory. AID gives it
    cardinality 0..1. **Optional.**

## 6. Consequences for the DMP (`aas-camel-dmp`, PLAN P5)

- Match the corrected IRIs (`hasInputSchema`, `hasOutputSchema`, …).
- Read `op` as a list. Without `op`, derive the operations as in §3.4. A
  property source observes when `observeproperty` is available, otherwise
  it reads.
- MQTT: accept AID's `mqv_controlPacket` with the consumer view, accept
  `mqv_responseTopic`, and drop `mqv_control_packet`, `mqv_request_reply`,
  `mqv_response_topic`, `mqtt_responseTopic` and `response.href`. Decode
  `.//` and `%23` in topics. Accept form `contentType`.
- HTTP: honour `htv_methodName`, accept `htv_headers`.
- Modbus: resolve `href` against `base` (AID: unit ID in the base), accept
  `modv_zeroBasedAddressing=false`, and treat `modv_pollingTime` as a lower
  limit for the polling interval.
- OPC UA: translate `uav_browsePath` into a NodeId
  (TranslateBrowsePathsToNodeIds).
- Regenerate the runtime-model fixtures (PLAN C4).

## 7. Order of work

1. `aas-model`: constants, `aid.py` (§3, §5), builders and tests.
2. `aas-camel-dmp`: projection and compiler (§6), fixtures, SPEC §5.2.
3. Regenerate the parent workspace's AAS descriptions.

Between steps 1 and 2, models newly generated by `aas-model` don't load in
the DMP.

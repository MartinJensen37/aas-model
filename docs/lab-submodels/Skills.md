# Skills

The skills of a resource: what it can do, how each skill is called, and what a skill made of other
skills runs. The resource ontology ARSO's control component (`https://w3id.org/2025/arso`, module
`skills.ttl`). It takes the place of IDTA 02015's Control Component Instance in a module and in a
component of a module (`aas_model.resource_template.modules`); the lab's MQTT and OPC UA stations
keep the Control Component Instance.

Classes: `aas_model.submodel_templates.arso.skills` (generated), `ModuleSkill` and `ModuleSkills`
(`aas_model.resource_template.modules`).

## Structure

```
Skills
├── {Skill}                       a skill; its kind and its type as supplemental semantic ids
│   ├── Deployment                Built | Described
│   ├── Start, Stop, Abort, Reset the commands
│   │   ├── InterfaceReference    the AID action that calls the command
│   │   ├── {Operation}           named like the command: Session and parameters in;
│   │   │                         Accepted, ErrorID and results out
│   │   └── Steps                 of a composite: what the command runs
│   │       └── {Step}            NodeId, Kind, Name, Order, Skill, Bindings, Outputs,
│   │                             Branches (parallel, decision), Condition, Steps
│   ├── Conditions                of a primitive: Precondition, Postcondition, Invariant
│   └── Completion                of a primitive: After, Timeout
├── RuleSet                       the rules the program is built by
└── Errors                        the codes an ErrorID can carry
```

## How it is used

- **Three kinds of skill**, told apart by a supplemental semantic id: `.../skill/Primitive` (one
  function block of the program moves one component: MoveAxis, Dispense, Weigh), `.../skill/Composite`
  (a module level skill whose steps run primitives: Dispensing), `.../skill/ModuleControl` (the
  module's own commands: Occupy, Release, Reset, Start, Stop, Abort, Clear). A second supplemental id
  says what the skill does (a skill type of the lab's vocabulary).
- **A primitive is in the AAS of the component it moves**, a composite in the module's. A step of a
  composite refers to the skill it runs by a model reference, so the steps of Dispensing lead into the
  pump's, the axis' and the scale's AASs. A component's commands refer to actions of its module's
  interface description: the module carries them out.
- **A command is called through its Operation.** The Operation delegates the call to the action named
  by `InterfaceReference` (the mapping configuration says how). Its input variables are `Session` (the
  occupation the caller holds) and the parameters; its outputs are `Accepted`, `ErrorID` and the
  results. A parameter carries `Unit`, `Minimum`, `Maximum` and `Default` as qualifiers, and what it
  means (a property of the vocabulary) as a supplemental semantic id. `Session`, `Accepted` and
  `ErrorID` carry `.../ControlComponent/Skill/OperationVariable/1/0`: they are the protocol, not
  parameters.
- **What a step hands its skill** is a binding per input of that skill: a constant (`Value`) or a
  variable of the command's own Operation (`SourceElement`), and the input itself (`InputReference`).
- **Deployment**: `Built` when the module's program carries the skill out, `Described` when it is in
  the AAS only. A described skill is built online by the integrator's tools; until then the capability
  it realizes is offered after a reconfiguration.

## Why it is shaped so

- **A skill is its commands.** An IEC 61499 skill is a state machine that is started, stopped,
  aborted and reset; each is called on its own and answers on its own. One Operation per skill (the
  Control Component Instance's) cannot say what stopping runs.
- **The steps use the Production Sequence's elements** (the same idShorts and semantic ids): a
  module's composition of skills and a product's recipe are read, drawn and edited by the same code
  (the process sequence planner and the skill editor of the web UI).
- **Primitives in the component's AAS:** every linear axis has the same two skills; a component kind
  is described once, wherever it is built in.
- **Conditions and Completion** are what a planner needs to compose new skills from primitives, and
  what the program checks while a primitive runs.
- **RuleSet** names the rules the program is built by, so a tool knows it can read the program back
  and build a described skill online. What was built in detail is the integrator's record, not the
  AAS's ([ControlConfiguration](ControlConfiguration.md)).

## Example

The filling module's Dispensing in iec61499-mgmt-py (`cell/modules/filling.yaml`, built by `modreg`):
a composite whose Start runs MoveAxis, Dispense, Home and Weigh of the axis', pump's and scale's AASs,
handing its own `Volume` to Dispense; its Stop runs Home.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `Skills`, semantic id `https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel`, version 1.0; template `templates/arso/Skills.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `{Skill}` | SMC | 0..* | `https://smartproductionlab.aau.dk/skill` | A named skill, an element of the Skills submodel itself, recognised by its semanticId (no idShort — the skill name is user-defined). |
| `{Skill}/Deployment` | Property (xs:string) | 0..1 | – | Built: the resource's program carries the skill out; Described: the skill is in the AAS only and is offered after a reconfiguration. |
| `{Skill}/SemanticId` | Property (xs:string) | 0..1 | – | What the skill does, as the short form of older AASs states it. |
| `{Skill}/Start` | SMC | 0..1 | – | One command of a skill: the action that calls it, its Operation, and what it runs. |
| `{Skill}/Start/InterfaceReference` | Ref | 0..1 | – | The AID action (arso:InterfaceSMC/InteractionMetadata/actions/{action}) that calls the command; in the short form, the action that starts the skill. |
| `{Skill}/Start/{SkillOperation}` | Operation | 0..* | – | Operation — the invocable Operation of a command (named like it), or in the short form of a skill (named like the skill). |
| `{Skill}/Start/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | What a command runs (or a branch, or the body of a conditional step): steps in the order of their Order. |
| `{Skill}/Start/Steps/{SkillStep}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Step/1/0` | One node of the flow. |
| `{Skill}/Start/Steps/{SkillStep}/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` |  |
| `{Skill}/Start/Steps/{SkillStep}/NodeId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0` | The node's identifier, unique in its command. |
| `{Skill}/Start/Steps/{SkillStep}/Kind` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Kind/1/0` | Step, parallel, decision or conditional. |
| `{Skill}/Start/Steps/{SkillStep}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | What a step, a branch or an output is called for a person; of a Binding, the input of the step's skill it is about. |
| `{Skill}/Start/Steps/{SkillStep}/Order` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | The position among its siblings, from 0; it decides the order, not the place in the collection. |
| `{Skill}/Start/Steps/{SkillStep}/Skill` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Skill/1/0` | The skill a step runs, the whole of it: running it is its Start, and its other commands are what ends it early. |
| `{Skill}/Start/Steps/{SkillStep}/Bindings` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Bindings/1/0` | What the inputs of the step's skill are handed. |
| `{Skill}/Start/Steps/{SkillStep}/Bindings/{StepBinding}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Binding/1/0` | One input of the step's skill (Name): a constant (Value) or a variable of the command's Operation (SourceElement). |
| `{Skill}/Start/Steps/{SkillStep}/Bindings/{StepBinding}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | What a step, a branch or an output is called for a person; of a Binding, the input of the step's skill it is about. |
| `{Skill}/Start/Steps/{SkillStep}/Bindings/{StepBinding}/Value` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0` | A constant: what a Binding hands to the input (the value as it runs), or what a Condition compares with. |
| `{Skill}/Start/Steps/{SkillStep}/Bindings/{StepBinding}/SourceElement` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0` | The variable of the command's Operation that is handed down to the input, or that a Condition looks at. |
| `{Skill}/Start/Steps/{SkillStep}/Bindings/{StepBinding}/InputReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/InputReference/1/0` | The input itself: the variable of the Start Operation of the step's skill. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Outputs/1/0` | The results of the command that this step gives. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Output/1/0` | One result: OutputId names the output variable of the command's Operation, ResultReference the result of the step's skill it is. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}/Name` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | What a step, a branch or an output is called for a person; of a Binding, the input of the step's skill it is about. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}/OutputId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0` | The output's identifier: the idShort of the output variable of the command's Operation. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}/DataType` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0` | Boolean, number or string. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}/Unit` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0` | The unit of an output or of what a Condition compares; empty for none. |
| `{Skill}/Start/Steps/{SkillStep}/Outputs/{StepOutput}/ResultReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ResultReference/1/0` | The result: an output variable of the Start Operation of the step's skill. |
| `{Skill}/Start/Steps/{SkillStep}/Branches` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Branches/1/0` | The branches of a parallel step (two or more, all have to end) or of a decision (exactly two). |
| `{Skill}/Start/Steps/{SkillStep}/Branches/{FlowBranch}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Branch/1/0` | One branch: BranchId, Name, Order and its Steps. |
| `{Skill}/Start/Steps/{SkillStep}/Branches/{FlowBranch}/Steps` | SMC | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` |  |
| `{Skill}/Start/Steps/{SkillStep}/Branches/{FlowBranch}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | What a step, a branch or an output is called for a person; of a Binding, the input of the step's skill it is about. |
| `{Skill}/Start/Steps/{SkillStep}/Branches/{FlowBranch}/Order` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | The position among its siblings, from 0; it decides the order, not the place in the collection. |
| `{Skill}/Start/Steps/{SkillStep}/Branches/{FlowBranch}/BranchId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/BranchId/1/0` | The branch's identifier, unique in its command. |
| `{Skill}/Start/Steps/{SkillStep}/Condition` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Condition/1/0` | What a decision or a conditional step looks at: every N-th run (ConditionType everyNthProduct: EveryNProducts, CounterScope), a comparison (ConditionType comparison: Operand, Operator, Expected, Unit), or a group (ConditionType all or any: Conditions). |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Order` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | The position among its siblings, from 0; it decides the order, not the place in the collection. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Unit` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Unit/1/0` | The unit of an output or of what a Condition compares; empty for none. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Conditions` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Conditions/1/0` | The conditions of a group: all of them hold (ConditionType all) or one does (any). |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Conditions/Condition` | SMC | 1..* | `https://smartproductionlab.aau.dk/ProductionSequence/Condition/1/0` |  |
| `{Skill}/Start/Steps/{SkillStep}/Condition/ConditionType` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ConditionType/1/0` | EveryNthProduct, comparison, all or any. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operator` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Operator/1/0` | Eq, ne, gt, gte, lt or lte. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/EveryNProducts` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/EveryNProducts/1/0` | The condition holds on every N-th run. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/CounterScope` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/CounterScope/1/0` | What the runs are counted over. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Expected` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Expected/1/0` | What the operand is compared with: DataType and Value. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Expected/Value` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0` | A constant: what a Binding hands to the input (the value as it runs), or what a Condition compares with. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Expected/DataType` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/DataType/1/0` | Boolean, number or string. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operand` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Operand/1/0` | What is compared: a variable of the command's Operation (OperandType parameter: SourceElement) or the output of an earlier step (OperandType output: StepId, OutputId). |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operand/SourceElement` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0` | The variable of the command's Operation that is handed down to the input, or that a Condition looks at. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operand/OutputId` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/OutputId/1/0` | The output's identifier: the idShort of the output variable of the command's Operation. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operand/OperandType` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/OperandType/1/0` | Parameter or output. |
| `{Skill}/Start/Steps/{SkillStep}/Condition/Operand/StepId` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/StepId/1/0` | The NodeId of the step whose output is compared. |
| `{Skill}/Stop` | SMC | 0..1 | – | One command of a skill: the action that calls it, its Operation, and what it runs. |
| `{Skill}/Stop/InterfaceReference` | Ref | 0..1 | – | The AID action (arso:InterfaceSMC/InteractionMetadata/actions/{action}) that calls the command; in the short form, the action that starts the skill. |
| `{Skill}/Stop/{SkillOperation}` | Operation | 0..* | – | Operation — the invocable Operation of a command (named like it), or in the short form of a skill (named like the skill). |
| `{Skill}/Stop/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | As `{Skill}/Start/Steps`. |
| `{Skill}/Abort` | SMC | 0..1 | – | One command of a skill: the action that calls it, its Operation, and what it runs. |
| `{Skill}/Abort/InterfaceReference` | Ref | 0..1 | – | The AID action (arso:InterfaceSMC/InteractionMetadata/actions/{action}) that calls the command; in the short form, the action that starts the skill. |
| `{Skill}/Abort/{SkillOperation}` | Operation | 0..* | – | Operation — the invocable Operation of a command (named like it), or in the short form of a skill (named like the skill). |
| `{Skill}/Abort/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | As `{Skill}/Start/Steps`. |
| `{Skill}/Reset` | SMC | 0..1 | – | One command of a skill: the action that calls it, its Operation, and what it runs. |
| `{Skill}/Reset/InterfaceReference` | Ref | 0..1 | – | The AID action (arso:InterfaceSMC/InteractionMetadata/actions/{action}) that calls the command; in the short form, the action that starts the skill. |
| `{Skill}/Reset/{SkillOperation}` | Operation | 0..* | – | Operation — the invocable Operation of a command (named like it), or in the short form of a skill (named like the skill). |
| `{Skill}/Reset/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | As `{Skill}/Start/Steps`. |
| `{Skill}/InterfaceReference` | Ref | 0..1 | – | The AID action (arso:InterfaceSMC/InteractionMetadata/actions/{action}) that calls the command; in the short form, the action that starts the skill. |
| `{Skill}/{SkillOperation}` | Operation | 0..* | – | Operation — the invocable Operation of a command (named like it), or in the short form of a skill (named like the skill). |
| `{Skill}/Conditions` | SMC | 0..1 | – | Of a primitive skill: Precondition, Postcondition, Invariant (css:Constraint), expressions over the resource's signals and the skill's parameters, checked as it runs. |
| `{Skill}/Conditions/Precondition` | Property (xs:string) | 0..1 | – | What has to hold when the skill starts. |
| `{Skill}/Conditions/Postcondition` | Property (xs:string) | 0..1 | – | The skill has succeeded when it holds (a sensor ends it). |
| `{Skill}/Conditions/Invariant` | Property (xs:string) | 0..1 | – | What has to hold all the while the skill runs. |
| `{Skill}/Completion` | SMC | 0..1 | – | Of a primitive skill: how it ends when no Postcondition ends it (After), and the longest it may run (Timeout). |
| `{Skill}/Completion/After` | Property (xs:string) | 0..1 | – | The open-loop duration: the skill has succeeded when it has passed, in seconds (a time ends it). |
| `{Skill}/Completion/Timeout` | Property (xs:string) | 0..1 | – | The longest the skill may run, a duration. |
| `{Skill}/StateMachine` | Property (xs:string) | 0..1 | – | Present only on asynchronous skills of the short form. |
| `RuleSet` | Property (xs:string) | 0..1 | – | The rule set the resource's program is built by, named by its URI. It says that the program can be read back by the rules and that a described skill can be built online; a tool that does not know the rule set does not change the program. |
| `Errors` | SMC | 1 | – | What the ErrorID in the answer of an Operation can be: one property per error. |
| `Errors/{SkillError}` | Property (xs:integer) | 0..* | – | A named error; its value is the code an ErrorID carries. |

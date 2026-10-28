# Bindings

A product's recipe bound to a line: per step of the recipe, the resource and the skill that carry it
out, and what each input of the skill is handed. The second submodel of a process AAS
(`aas_model.process_template.Process`).

Classes: `aas_model.submodel_templates.process.bindings` (generated). They have names of their own
(`ProcessBindings`, `ProcessStepBinding`, `InputBinding`, `InputBindings`, `BoundStep`, `BoundSkill`):
the skills and the recipe have elements with the same idShorts and other content, and aas_pydantic
reads an element back as the class its dump names.

## How it is used

- **One step binding per step of the recipe,** named by the step's `NodeId`: `Step` refers to the
  step in the product's Production Sequence, `Resource` to the AAS of the module that carries it out,
  `Skill` to the skill in that module's [Skills](Skills.md), `ExecutionMode` says `station` (or
  `manual`, with no resource and skill).
- **One binding per input the skill is handed something:** `Name` names the input, `SourceElement`
  refers to the product's element whose value it takes (a parameter of its
  [Process Parameters](ProcessParameters.md)), or `Value` is a constant; `InputReference` refers to the
  input itself, a variable of the Operation of the skill's Start. An input that is not bound runs with
  its default.
- **Checked by following the references** (iec61499-mgmt-py, `cell/examples/plan_check.py`,
  `check_process`): the step's process requires a capability the resource offers, realized by this
  skill, with properties that cover the product's values; each bound input exists, takes a value in
  its unit and within its limits; every step of the recipe is bound. The result is the
  [Validation](Validation.md).

## Why it is shaped so

- **The elements are the planner's** (the Production Sequence's semantic ids): a step binding holds
  what the planner writes into a step of the recipe today, moved out of the product.
- **Every link is a model reference,** so a reader goes from the binding into the product's and the
  resources' AASs without knowing their names, and a check can tell a broken link.
- **`InputReference` names the input,** not only its name: a renamed or removed input is found, and
  the input's meaning (its supplemental semantic id) can be compared with the source's.

## Example

The 2 mL vial on the filling line in iec61499-mgmt-py
(`cell/examples/processes/vial_2ml_on_filling_line.py`): Filling bound to the filling module's
Dispensing, its Volume taken from the vial's FillVolume; Stoppering, Capping and Inspection bound to
the modules of the same names, handed nothing.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `Bindings`, semantic id `https://smartproductionlab.aau.dk/ProcessBindings/1/0/Submodel`, version 1.0; template `templates/process/Bindings.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `{StepBinding}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProcessBindings/StepBinding/1/0` | The binding of one step of the recipe, named by the step's NodeId. |
| `{StepBinding}/NodeId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0` | The NodeId of the step in the recipe. |
| `{StepBinding}/Step` | Ref | 1 | `https://smartproductionlab.aau.dk/ProcessBindings/Step/1/0` | The step in the product's recipe (Production Sequence). |
| `{StepBinding}/Resource` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Resource/1/0` | The resource that carries the step out (a model reference to its AAS); none for a manual step. |
| `{StepBinding}/Skill` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Skill/1/0` | The skill of the resource that carries the step out; none for a manual step. |
| `{StepBinding}/ExecutionMode` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/ExecutionMode/1/0` | How the step is carried out: station (by a resource's skill) or manual. |
| `{StepBinding}/Bindings` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Bindings/1/0` | What the skill's inputs are handed. |
| `{StepBinding}/Bindings/{Binding}` | SMC | 1..* | `https://smartproductionlab.aau.dk/ProductionSequence/Binding/1/0` | What one input of the skill is handed: a process parameter of the product, or a constant. |
| `{StepBinding}/Bindings/{Binding}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name of the skill's input. |
| `{StepBinding}/Bindings/{Binding}/SourceElement` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0` | The product's element whose value the input takes (a process parameter of its Process Parameters). |
| `{StepBinding}/Bindings/{Binding}/Value` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0` | The constant the input takes, when no SourceElement is given. |
| `{StepBinding}/Bindings/{Binding}/InputReference` | Ref | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/InputReference/1/0` | The input itself: a variable of the Operation of the skill's Start command. |

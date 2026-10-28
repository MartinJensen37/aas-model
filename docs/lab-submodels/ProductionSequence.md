# Production Sequence

A product's recipe: the steps that make it, in order, each running a process of its Process
Parameters, with calls of the recipes of its parts, parallel branches and steps that run only
sometimes (every N-th product). The process sequence planner's submodel (basyx-aas-web-ui, module
ProcessSequence), version 2.0; in the product AAS (`aas_model.product_template.Product`).

Classes: `aas_model.submodel_templates.product.production_sequence` (generated).

## How it is used

- **The submodel's id** is the product AAS's id, base64url-encoded, below
  `https://smartproductionlab.aau.dk/sm/process-plan/` (`aas_model.product_template.plan_id`): the
  planner finds a product's recipe by it. `Subject` names the product's AAS, `Revision` counts the
  saved changes.
- **A step** (Kind `step`) refers to its process (`ProcessReference`, in `ProcessOwner`'s Process
  Parameters) and the capabilities it requires (`RequiredCapabilities`).
- **A call** (Kind `call`) runs the recipe of a part (`SequenceReference`, `Component`); a
  **parallel** node has `Branches`; a **conditional** node guards `Steps` with a `Condition`.
- **The equipment is the process AAS's.** In the lab's reference products a step names no resource,
  skill or binding: [Bindings](Bindings.md) of the process AAS bind each step to a resource and a
  skill. The planner still writes `Resource`, `SkillId`, `Skill`, `ExecutionMode` and `Bindings` into
  the step itself, which the template keeps for it.

## Why it is shaped so

- **The planner's own structure, kept:** the web UI reads and writes it, and a module's composite
  skill uses the same step elements ([Skills](Skills.md)), so one editor and one reader serve both.
- **The recipe without equipment** (ISA-88's general recipe): the product stays the same when the line
  changes; the same recipe is bound to two lines by two process AASs.

## Example

The 2 mL vial in iec61499-mgmt-py (`cell/examples/products/vial_2ml.py`): Filling, Stoppering,
Capping, Inspection, in that order.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `ProductionSequence`, semantic id `https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/2/0`, version 2.0; template `templates/product/ProductionSequence.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `PlanSchema` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/PlanSchema/1/0` | The schema of the plan: production-sequence/2.0. |
| `Revision` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Revision/1/0` | Counts the saved changes of the plan. |
| `SequenceId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/SequenceId/1/0` | Identifies the sequence among those of its subject. |
| `Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the sequence. |
| `Role` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Role/1/0` | Primary: the subject's own sequence. Subprocess: a sequence others call. |
| `Subject` | Ref | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Subject/1/0` | The AAS of the product the sequence plans. |
| `Subprocesses` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Subprocesses/1/0` | The sequences this one calls. |
| `Subprocesses/{Subprocess}` | Ref | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/SequenceReference/1/0` | A called sequence (its submodel). |
| `Steps` | SMC | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | The nodes of the sequence. |
| `Steps/{Step}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Step/1/0` | One node of the sequence. Kind step: a process run by a skill of a resource. Kind call: another sequence. Kind parallel: branches that all join. Kind conditional: steps that only run when the condition holds. |
| `Steps/{Step}/NodeId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0` | Identifies the node within its sequence. |
| `Steps/{Step}/Kind` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Kind/1/0` | step, call, parallel or conditional. |
| `Steps/{Step}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the node. |
| `Steps/{Step}/Order` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | Position among the nodes beside it. |
| `Steps/{Step}/ProcessOwner` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessOwner/1/0` | Kind step: the AAS whose process the step runs. |
| `Steps/{Step}/ProcessReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ProcessReference/1/0` | Kind step: the process, in the owner's Process Parameters. |
| `Steps/{Step}/RequiredCapabilities` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapabilities/1/0` | Kind step: the capabilities the step requires, where they differ from those of its process. |
| `Steps/{Step}/RequiredCapabilities/{RequiredCapability}` | Ref | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/RequiredCapability/1/0` | A Required capability in a Capability Description. |
| `Steps/{Step}/Resource` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Resource/1/0` | Kind step: the AAS of the resource the step is assigned to. |
| `Steps/{Step}/SkillId` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SkillId/1/0` | Kind step: the name of the skill that runs the step. |
| `Steps/{Step}/Skill` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Skill/1/0` | Kind step: the skill, in the resource's Skills submodel. |
| `Steps/{Step}/ExecutionMode` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/ExecutionMode/1/0` | Kind step: station (a resource runs it) or manual. |
| `Steps/{Step}/Bindings` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Bindings/1/0` | Kind step: what is bound to the parameters of the skill. |
| `Steps/{Step}/Bindings/{Binding}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Binding/1/0` | What one parameter of the step's skill gets: a constant, or a process parameter. |
| `Steps/{Step}/Bindings/{Binding}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The parameter of the skill. |
| `Steps/{Step}/Bindings/{Binding}/Value` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0` | The constant; empty when the value comes from a source. |
| `Steps/{Step}/Bindings/{Binding}/SourceAas` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceAas/1/0` | The AAS the value comes from. |
| `Steps/{Step}/Bindings/{Binding}/SourceElement` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0` | The element the value comes from. |
| `Steps/{Step}/SequenceReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SequenceReference/1/0` | Kind call: the sequence that is run. |
| `Steps/{Step}/OccurrenceId` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/OccurrenceId/1/0` | Kind call: identifies this use of the called sequence. |
| `Steps/{Step}/Component` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Component/1/0` | Kind call: the part the called sequence makes. |
| `Steps/{Step}/Component/GlobalAssetId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/GlobalAssetId/1/0` | The part's global asset id. |
| `Steps/{Step}/Component/SourceAas` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceAas/1/0` | The AAS the part comes from. |
| `Steps/{Step}/Component/SourceElement` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0` | The element the part comes from. |
| `Steps/{Step}/Condition` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Condition/1/0` | Kind conditional: when the guarded steps run. |
| `Steps/{Step}/Condition/ConditionType` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/ConditionType/1/0` | The kind of condition, e.g. everyNthProduct. |
| `Steps/{Step}/Condition/EveryNProducts` | Property (xs:positiveInteger) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/EveryNProducts/1/0` | everyNthProduct: every how many products. |
| `Steps/{Step}/Condition/CounterScope` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/CounterScope/1/0` | everyNthProduct: what the count runs over, e.g. productionRun. |
| `Steps/{Step}/Steps` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | Kind conditional: the guarded steps, each a Step as described here. |
| `Steps/{Step}/Branches` | SMC | 0..1 | `https://smartproductionlab.aau.dk/ProductionSequence/Branches/1/0` | Kind parallel: the branches. |
| `Steps/{Step}/Branches/{Branch}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProductionSequence/Branch/1/0` | One branch of a parallel node. |
| `Steps/{Step}/Branches/{Branch}/BranchId` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/BranchId/1/0` | Identifies the branch. |
| `Steps/{Step}/Branches/{Branch}/Name` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0` | The name shown for the branch. |
| `Steps/{Step}/Branches/{Branch}/Order` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Order/1/0` | Position among the branches. |
| `Steps/{Step}/Branches/{Branch}/Steps` | SMC | 1 | `https://smartproductionlab.aau.dk/ProductionSequence/Steps/1/0` | The steps of the branch, each a Step as described here. |

# Process Information

What a process AAS binds: the product, the production system and the recipe, the recipe's revision,
and how far the binding is. The first submodel of a process AAS
(`aas_model.process_template.Process`), ISA-88's master recipe: a product's recipe bound to one line.

Classes: `aas_model.submodel_templates.process.process_information` (generated).

## How it is used

- `Product` and `Line` refer to the product's and the line's AASs; `Recipe` to the product's
  [Production Sequence](ProductionSequence.md) submodel.
- `RecipeRevision` is the recipe's `Revision` the bindings were made for. A newer recipe has to be
  bound again.
- `Status`: `Draft` while it is being bound, `Approved` once the line engineer has approved it,
  `Withdrawn` when it is no longer to be used.
- The process AAS's shell names the product's and the line's assets as specific asset ids
  (`product`, `line`), so the processes of a product, or of a line, are found by asset id.

## Why it is shaped so

- **A process AAS of its own,** apart from the product's and the resources': a reconfiguration of the
  line changes the resources and at most the process AAS, never the product; one product on two lines
  is two process AASs and one product AAS; the product designer, the line engineer and the vendor
  each own one AAS.
- **The revision is recorded** because bindings name the recipe's steps: a changed recipe can leave a
  binding pointing at a step that is gone.
- Approval by whom and when, and the candidates the matching found, are to come.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `ProcessInformation`, semantic id `https://smartproductionlab.aau.dk/ProcessInformation/1/0/Submodel`, version 1.0; template `templates/process/ProcessInformation.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `Product` | Ref | 1 | `https://smartproductionlab.aau.dk/ProcessInformation/Product/1/0` | The product whose recipe is bound (a model reference to its AAS). |
| `Line` | Ref | 1 | `https://smartproductionlab.aau.dk/ProcessInformation/Line/1/0` | The production system the recipe is bound to (a model reference to its AAS). |
| `Recipe` | Ref | 1 | `https://smartproductionlab.aau.dk/ProcessInformation/Recipe/1/0` | The recipe that is bound: the product's Production Sequence submodel. |
| `RecipeRevision` | Property (xs:nonNegativeInteger) | 1 | `https://smartproductionlab.aau.dk/ProcessInformation/RecipeRevision/1/0` | The revision of the recipe the bindings were made for; a newer recipe needs binding again. |
| `Status` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProcessInformation/Status/1/0` | Where the binding stands: Draft, Approved or Withdrawn. |

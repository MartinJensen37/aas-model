# Validation

Whether a process AAS's bound recipe fits the line: the check's result and what it found. The third
submodel of a process AAS (`aas_model.process_template.Process`).

Classes: `aas_model.submodel_templates.process.validation` (generated).

## How it is used

- `Result` is `Fits` or `DoesNotFit`; `CheckedBy` names the check (`plan_check`); `Findings` holds one
  text per thing that does not hold (none when it fits): "Filling: ContainerType = syringe is not
  covered by Filling".
- It is written when the bindings are made or the line changes. In iec61499-mgmt-py the reference
  processes state theirs, and building them refuses one whose Validation is not what the check finds
  (`cell/examples/example_line.py`).

## Why it is shaped so

- **The result is kept with the binding,** so whoever runs the process (an operator, an agent) sees
  that it was checked against the line as it was, and a reconfiguration that breaks it shows.
- **Findings as plain texts** for now; when and by whom, and the line's state it was checked against,
  are to come.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `Validation`, semantic id `https://smartproductionlab.aau.dk/ProcessValidation/1/0/Submodel`, version 1.0; template `templates/process/Validation.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `Result` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProcessValidation/Result/1/0` | Fits, or DoesNotFit. |
| `CheckedBy` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProcessValidation/CheckedBy/1/0` | The check that gave the result. |
| `Findings` | SML of Property | 0..1 | `https://smartproductionlab.aau.dk/ProcessValidation/Findings/1/0` | What the check found, one text per finding; empty when the recipe fits. |
| `Findings/{Finding}` | Property (xs:string) | 0..* | `https://smartproductionlab.aau.dk/ProcessValidation/Finding/1/0` | One thing the check found. |

# Parameters

The settings of a resource that are not a skill's: a value each, with its unit and the interface
property it is written through (microsteps of a drive, a speed, a timeout). ARSO's `parameters.ttl`.

Classes: `aas_model.submodel_templates.arso.parameters` (generated). A `Module` may hold it
(`parameters`); a module described from its spec does not yet.

## How it is used

A parameter entry is named by the user. `Value` is the value the resource runs with, its
`valueType` the parameter's type; `Unit` its unit; `InterfaceReference` the property of the asset
interface description it is read and written through.

## Why it is shaped so

- **Not a skill's parameters.** A skill's parameters are the input variables of its Start's
  Operation, with their limits and default (see [Skills](Skills.md)); they change with each call.
  Parameters here change when the resource is set up.
- **Not aas-model's Parameters.** The lab's stations keep a `Location` group there; where a module is,
  is a coordinate in its Variables (`Measurements/Coordinates`, see `docs/lab-aas.md`).
- **Fixed facts of the machine** (a screw's lead, a motor's current) belong in IDTA 02003 Technical
  Data, not here.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `Parameters`, semantic id `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel`, version 1.0; template `templates/arso/Parameters.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `{ParameterEntry}` | SMC | 1..* | – | A named parameter entry. |
| `{ParameterEntry}/InterfaceReference` | Ref | 0..1 | – | Points to an AID property (.../InteractionMetadata/properties/{key}) in the same AAS (parameters_builder.py hardcodes the properties path segment, never actions/events). |
| `{ParameterEntry}/Value` | Property (xs:string) | 0..1 | – | The parameter's value as deployed; its valueType is the parameter's type (added 2 Oct 2026 for the registration service). |
| `{ParameterEntry}/Unit` | Property (xs:string) | 0..1 | – | The unit of the value (added 2 Oct 2026). |

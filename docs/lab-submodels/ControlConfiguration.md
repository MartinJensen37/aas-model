# Control Configuration

What was built on a resource's controller: from which source and by which rules its program was
generated, which block of the program is which skill and step, the types in use with their hashes,
and whether the running program is still the one its source generates. ARSO's
`control-configuration.ttl`.

Classes: `aas_model.submodel_templates.arso.control_configuration` (generated),
`ModuleControlConfiguration` (`aas_model.resource_template.modules`; its `SyncState` is `NotRead`
until the controller is read).

## How it is used

The integrator's tools write it when they build or read a module (in iec61499-mgmt-py: `modsync`,
`modreg profile --record`):

- `ModuleSpec`, `Target`, `Generator`, `ProgramDigest`: what the program was generated from, for
  which controller, by which generator, and a digest of the generated program.
- `Rules`: the rule set it was built by.
- `Instances`: per skill and per step of a command, the block of the program that carries it out
  (instance path, type, type hash) and a reference to the skill or step it is.
- `Types`: the function block types in use, with the hash the runtime reports.
- `SyncState` and `Differences`: `InSync`, `Drift` (with one entry per difference), `NoProgram` or
  `NotRead`.
- `ActiveProcedure`, `ChangeLog`: the process whose procedure is active, and one record per
  reconfiguration.

## Why it is shaped so

- **It is the integrator's record, kept outside the AAS** (ARSO 0.10). The AAS says what the
  module should do (its skills, with `Deployment` Built or Described, and the `RuleSet`); the record
  says how that was built, block by block, and changes with every build. A module's `Module` type
  holds it as optional (`control_configuration`), and the reference modules leave it out.
- **Instances refer to skills and steps by model reference**, so a tool goes from a block of the
  running program to the skill in the AAS and back, without names agreeing by convention.
- **Hashes** let a tool see that a type on the controller is not the one it built, without reading
  the type.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `ControlConfiguration`, semantic id `https://smartproductionlab.aau.dk/ARSO/ControlConfiguration/1/0/Submodel`, version 1.0; template `templates/arso/ControlConfiguration.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `Runtime` | SMC | 0..1 | – | The controller runtime: Name, ManagementEndpoint, Resource. |
| `Runtime/Name` | Property (xs:string) | 0..1 | – | Property Name, ManagementEndpoint or Resource of the runtime. |
| `Runtime/ManagementEndpoint` | Property (xs:string) | 0..1 | – | Property Name, ManagementEndpoint or Resource of the runtime. |
| `Runtime/Resource` | Property (xs:string) | 0..1 | – | Property Name, ManagementEndpoint or Resource of the runtime. |
| `Rules` | Property (xs:string) | 0..1 | – | The IRI of the rule set the resource's program is built by: its shell, the interface of a skill primitive and the pattern of a composite skill. |
| `ModuleSpec` | Property (xs:string) | 0..1 | – | Property ModuleSpec, Target, Generator (what the program was generated from and by), ProgramDigest (SHA-256 of the generated program: instances, types, connections, values) or ReadAt (when the controller was read). |
| `Target` | Property (xs:string) | 0..1 | – | Property ModuleSpec, Target, Generator (what the program was generated from and by), ProgramDigest (SHA-256 of the generated program: instances, types, connections, values) or ReadAt (when the controller was read). |
| `Generator` | Property (xs:string) | 0..1 | – | Property ModuleSpec, Target, Generator (what the program was generated from and by), ProgramDigest (SHA-256 of the generated program: instances, types, connections, values) or ReadAt (when the controller was read). |
| `ProgramDigest` | Property (xs:string) | 0..1 | – | Property ModuleSpec, Target, Generator (what the program was generated from and by), ProgramDigest (SHA-256 of the generated program: instances, types, connections, values) or ReadAt (when the controller was read). |
| `ReadAt` | Property (xs:string) | 0..1 | – | Property ModuleSpec, Target, Generator (what the program was generated from and by), ProgramDigest (SHA-256 of the generated program: instances, types, connections, values) or ReadAt (when the controller was read). |
| `SyncState` | Property (xs:string) | 1 | – | InSync (the running program is the one its source generates), Drift (it differs, see Differences), NoProgram, NotRead (described from the source only). |
| `Differences` | SMC | 0..1 | – | One Property per difference between the running program and its source. |
| `Differences/{CCfgDifference}` | Property (xs:string) | 0..* | – | One difference. |
| `Types` | SMC | 0..1 | – | The function block types in use, each with Name and Hash as the runtime reports them. |
| `Types/{CCfgType}` | SMC | 0..* | – | One function block type in use. |
| `Types/{CCfgType}/Name` | Property (xs:string) | 0..1 | – | Property Name or Hash of a type, as the runtime reports them. |
| `Types/{CCfgType}/Hash` | Property (xs:string) | 0..1 | – | Property Name or Hash of a type, as the runtime reports them. |
| `Instances` | SMC | 0..1 | – | The blocks of the program that are the resource's skills and the steps of their commands: which block, of which type, is which skill. |
| `Instances/{CCfgInstance}` | SMC | 0..* | – | One block of the program, named like its instance path with underscores. |
| `Instances/{CCfgInstance}/InstancePath` | Property (xs:string) | 0..1 | – | Property InstancePath (the dotted name of the instance), FBType (its qualified IEC 61499 type) or TypeHash (the hash of that type as the runtime reports it). |
| `Instances/{CCfgInstance}/FBType` | Property (xs:string) | 0..1 | – | Property InstancePath (the dotted name of the instance), FBType (its qualified IEC 61499 type) or TypeHash (the hash of that type as the runtime reports it). |
| `Instances/{CCfgInstance}/TypeHash` | Property (xs:string) | 0..1 | – | Property InstancePath (the dotted name of the instance), FBType (its qualified IEC 61499 type) or TypeHash (the hash of that type as the runtime reports it). |
| `Instances/{CCfgInstance}/Skill` | Ref | 0..1 | – | What the block is: a skill (in the Skills submodel of this AAS or of a component), or the step of a command that runs one. |
| `ActiveProcedure` | SMC | 0..1 | – | Reference to the Process AAS (and version) whose procedure is active, with NetworkHash, BootFileHash, ActivatedAt. |
| `ChangeLog` | SML of SubmodelElementCollection | 0..1 | – | One Change SMC per reconfiguration: Time, Trigger, ChangeClass (a pprl:ChangeClass IRI), From, To, Result, Duration. |
| `ChangeLog/{CCfgChange}` | SMC | 0..* | – | One reconfiguration record. |

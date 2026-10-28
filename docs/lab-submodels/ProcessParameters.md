# Process Parameters

The processes a product needs, each with the product's values for it, the materials it uses and the
capability it requires. IDTA 02031-1 (Process Parameters) with the lab's extension; in the product
AAS (`aas_model.product_template.Product`).

Classes: `aas_model.submodel_templates.product.process_parameters` (generated). The process's own
`ProcessParameters` collection is the class `ProcessParameterGroup`, named apart from the submodel.

## How it is used

- **A process** (`Filling`, `Stoppering`, ...) has IDTA's identification (`ProcessId`, `ProcessName`,
  `ProcessDescription`, `PlannedProcessTime`) and three groups of parameters. The product's values go
  into `ProductParameters` (the fill volume, the container type, the stopper's diameter); each is a
  Property whose semantic id is a property of the lab's vocabulary (`.../semantics/FillVolume`) and
  whose unit is a `Unit` qualifier.
- **`ProcessBoM`** (extension) lists what the process uses: per material a reference to the entity of
  the product's bill of material, its role (`workpiece` it works on, `incorporated` into the product,
  `output` it makes) and how much, fixed (`Quantity`, `Unit`) or as a parameter
  (`QuantityParameterReference`: the liquid a filling uses is its FillVolume).
- **`RequiredCapability`** (extension) refers to the Required capability in the product's Capability
  Description (IDTA 02020) that a resource has to offer for the process.
- A binding of a process AAS hands a value from here to a skill's input
  ([Bindings](Bindings.md)).

## Why it is shaped so

- **IDTA 02031-1 as published, extended, not changed:** its readers find what they expect.
- **Parameters as Properties with the vocabulary's ids:** a parameter, the required capability's
  property and a skill's input that mean the same carry the same id, so matching and binding go by
  meaning, not by name.
- **MaterialUse** says what goes into the product at which process, which IDTA leaves to the process
  description; the batch record later needs it per item.
- **The required capability is referenced, not repeated:** its values and acceptable ranges are in
  the Capability Description, where resources' offered capabilities are described alike.

## Example

The 2 mL vial in iec61499-mgmt-py (`cell/examples/products/vial_2ml.py`): Filling with ContainerType
`vial`, GraspDiameter 16 mm and FillVolume 2 mL; the vial as workpiece, the liquid incorporated as much
as FillVolume.

## Elements

<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->

**Submodel** `ProcessParameters`, semantic id `https://admin-shell-io/idta/SubmodelTemplate/ProcessParameters/1/0`, version 1.0; template `templates/product/ProcessParameters.json`.

| Element (path) | Kind | Card. | Semantic id | Description |
| --- | --- | --- | --- | --- |
| `Processes` | SMC | 1 | `https://admin-shell.io/idta/ProcessParameters/Processes/1/0` | Provides all the necessary parameters of processes in a structured form that are required to manufacture a product |
| `Processes/{Process}` | SMC | 0..* | `https://admin-shell.io/idta/ProcessParameters/Process/1/0` | The processes to be executed are described individually in the SMC Process. |
| `Processes/{Process}/ProcessId` | Property (xs:string) | 1 | `https://admin-shell.io/idta/ProcessParameters/ProcessId/1/0` | Describes the ID of the process |
| `Processes/{Process}/ProcessName` | Property (xs:string) | 1 | `https://admin-shell.io/idta/ProcessParameters/ProcessName/1/0` | Describes the Name of the Process |
| `Processes/{Process}/ProcessDescription` | MLP | 1 | `https://admin-shell.io/idta/ProcessParameters/ProcessDescription/1/0` | Describes the process. |
| `Processes/{Process}/PlannedProcessTime` | Property (xs:duration) | 1 | `https://admin-shell.io/idta/ProcessParameters/PlannedProcessTime/1/0` | Planned processing time for process execution (without set-up time) |
| `Processes/{Process}/ProductParameters` | SMC | 1 | `https://admin-shell.io/idta/ProcessParameters/ProductParameters/1/0` | Mandatory product parameters for process execution |
| `Processes/{Process}/ProductParameters/{Parameter}` | Property (xs:string) | 0..* | – | One parameter, named by its idShort; its semanticId says what it means. |
| `Processes/{Process}/ProcessParameters` | SMC | 1 | `https://admin-shell.io/idta/ProcessParameters/ProcessParameters/1/0` | Mandatory process parameters for process execution |
| `Processes/{Process}/ProcessParameters/{Parameter}` | Property (xs:string) | 0..* | – | One parameter, named by its idShort; its semanticId says what it means. |
| `Processes/{Process}/ResourceParameters` | SMC | 1 | `https://admin-shell.io/idta/ProcessParameters/ResourceParameters/1/0` | Mandatory resource parameters for process execution |
| `Processes/{Process}/ResourceParameters/{Parameter}` | Property (xs:string) | 0..* | – | One parameter, named by its idShort; its semanticId says what it means. |
| `Processes/{Process}/ProcessBoM` | SMC | 1 | `https://admin-shell.io/idta/ProcessParameters/ProcessBoM/1/0` | Describes the products or semi-finished products to be involved in the process |
| `Processes/{Process}/ProcessBoM/{MaterialUse}` | SMC | 0..* | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/1/0` | Lab extension: one material the process uses or makes. |
| `Processes/{Process}/ProcessBoM/{MaterialUse}/MaterialReference` | Ref | 1 | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/MaterialReference/1/0` | The material: an entity of the bill of material. |
| `Processes/{Process}/ProcessBoM/{MaterialUse}/Role` | Property (xs:string) | 1 | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/Role/1/0` | workpiece, incorporated or output. |
| `Processes/{Process}/ProcessBoM/{MaterialUse}/Quantity` | Property (xs:double) | 0..1 | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/Quantity/1/0` | How much of the material. |
| `Processes/{Process}/ProcessBoM/{MaterialUse}/Unit` | Property (xs:string) | 0..1 | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/Unit/1/0` | The unit of the quantity. |
| `Processes/{Process}/ProcessBoM/{MaterialUse}/QuantityParameterReference` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProcessParameters/MaterialUse/QuantityParameterReference/1/0` | The parameter that gives the quantity, instead of a fixed one. |
| `Processes/{Process}/RequiredCapability` | Ref | 0..1 | `https://smartproductionlab.aau.dk/ProcessParameters/RequiredCapability/1/0` | Lab extension: the Required capability the process needs, in the Capability Description of the same AAS. |

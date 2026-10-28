# The lab's product, process and resource AASs

aas-model's types and submodels for the AASs of the lab's modules, products and processes, beside
the stations (`resource_template.stations`, `resource_instances`). The split follows ISA-88's recipe
levels:

| AAS | ISA-88 | One per | Says | Type |
| --- | --- | --- | --- | --- |
| Product | General recipe | product, and each part with a recipe of its own | what the product is, the processes it needs and the capabilities they require, its recipe; no equipment | `aas_model.product_template.Product` |
| Process | Master recipe | product and line | the recipe bound to one line: per step the resource, the skill and its inputs; whether it fits | `aas_model.process_template.Process` |
| Resource | (equipment) | line, module, component | what it offers and how it is called, what its skills are made of, its live values and where it is | `aas_model.resource_template.modules`: `ProductionSystem`, `Module`, `Component` |

Why three: a reconfiguration of a line changes the resources and at most the process AAS, never the
product; one product on two lines is two process AASs and one product AAS; the product designer, the
line engineer and the vendor each own one AAS.

The resource types follow the resource ontology ARSO (`https://w3id.org/2025/arso`), which
iec61499-mgmt-py keeps (`ontology/ARSO`); the instances of the lab's reference line are built there
too (`cell/examples/example_line.py`).

## The types and their submodels

| Type | Asset kind, asset type | Submodels |
| --- | --- | --- |
| `Module` | Instance, `.../Resource/Module` | Nameplate, Hierarchical Structures (its components), Asset Interfaces Description (one OPC UA server), Asset Interfaces Mapping Configuration, [Skills](lab-submodels/Skills.md), [Variables](#variables-and-coordinates), Capability Description (offered; optional); optional [Control Configuration](lab-submodels/ControlConfiguration.md) and [Parameters](lab-submodels/Parameters.md) |
| `Component` | Instance, `.../Resource/Component/<Kind>` | [Skills](lab-submodels/Skills.md): its primitives, which its module carries out |
| `ProductionSystem` | Instance, `.../Resource/System` | Hierarchical Structures (its modules, each by its asset id); optional [Variables](#variables-and-coordinates) with the coordinates of its own points |
| `Product` | Type, `.../Product` | Nameplate, Hierarchical Structures (its bill of material; a part states its `Quantity` and `QuantityUnit`), [Process Parameters](lab-submodels/ProcessParameters.md), Capability Description (required), [Production Sequence](lab-submodels/ProductionSequence.md) |
| `Process` | Type, `.../Process` | [Process Information](lab-submodels/ProcessInformation.md), [Bindings](lab-submodels/Bindings.md), [Validation](lab-submodels/Validation.md) |

`Module`, `Component` and `ProductionSystem` are `Resource`s (through `ArsoResource`); a submodel of
`Resource` a kind does not have is left out (`None`). What changes from IDTA's templates
(`resource_template/modules/submodels.py`):

- **Capability Description (IDTA 02020):** a capability is realized by a skill of the same AAS or a
  component's (`RealizedBySkill`, a model reference where IDTA leaves an external one); a property is
  the variable of the module it is (`SameAs`); a constraint is a `BasicConstraint` expression. A
  property may list the values a module takes (IDTA's `SubmodelElementList` kind: the containers
  vial, syringe, cartridge).
- **Asset Interfaces Description:** one OPC UA interface (`ModuleInterfaces`).
- **Hierarchical Structures:** parts that have parts in turn (`LocatedNode`). Where a part is, is a
  coordinate, not a statement of the node.
- **Nameplate:** the lab's (`lab_nameplate`), for each instance to state its own values in.

## Submodels that are the lab's own

| Submodel | Semantic id | Template | Classes | Description |
| --- | --- | --- | --- | --- |
| Skills | `https://smartproductionlab.aau.dk/ARSO/Skills/1/0/Submodel` | `templates/arso/Skills.json` | `submodel_templates.arso.skills` | [Skills](lab-submodels/Skills.md) |
| Parameters | `https://smartproductionlab.aau.dk/ARSO/Parameters/1/0/Submodel` | `templates/arso/Parameters.json` | `submodel_templates.arso.parameters` | [Parameters](lab-submodels/Parameters.md) |
| Control Configuration | `https://smartproductionlab.aau.dk/ARSO/ControlConfiguration/1/0/Submodel` | `templates/arso/ControlConfiguration.json` | `submodel_templates.arso.control_configuration` | [Control Configuration](lab-submodels/ControlConfiguration.md) |
| Process Parameters (IDTA 02031-1, extended) | `https://admin-shell-io/idta/SubmodelTemplate/ProcessParameters/1/0` | `templates/product/ProcessParameters.json` | `submodel_templates.product.process_parameters` | [Process Parameters](lab-submodels/ProcessParameters.md) |
| Production Sequence | `https://smartproductionlab.aau.dk/SubmodelTemplate/ProductionSequence/2/0` | `templates/product/ProductionSequence.json` | `submodel_templates.product.production_sequence` | [Production Sequence](lab-submodels/ProductionSequence.md) |
| Process Information | `https://smartproductionlab.aau.dk/ProcessInformation/1/0/Submodel` | `templates/process/ProcessInformation.json` | `submodel_templates.process.process_information` | [Process Information](lab-submodels/ProcessInformation.md) |
| Bindings | `https://smartproductionlab.aau.dk/ProcessBindings/1/0/Submodel` | `templates/process/Bindings.json` | `submodel_templates.process.bindings` | [Bindings](lab-submodels/Bindings.md) |
| Validation | `https://smartproductionlab.aau.dk/ProcessValidation/1/0/Submodel` | `templates/process/Validation.json` | `submodel_templates.process.validation` | [Validation](lab-submodels/Validation.md) |
| Variables, with Coordinates | `https://smartproductionlab.aau.dk/submodels/Variables/1/0` | none (hand-written classes) | `submodel_templates.variables`, `submodel_templates.coordinates` | [below](#variables-and-coordinates) |

**How they are made:**

```
ontology ARSO --modreg generate (iec61499-mgmt-py)--> templates/arso/*.json
templates/{arso,product,process}/*.json --scripts/lab_generate.py--> submodel_templates/{arso,product,process}/*.py
templates/... + docs/lab-submodels/*.md --scripts/lab_docs.py--> the element tables of the descriptions
```

The templates of the product and the process are kept as files: the planner's Production Sequence,
IDTA 02031-1 with the lab's extension, and the process AAS's three (written by hand until the process
ontology is remade). `tests/test_lab_templates.py` fails when the classes or the descriptions are not
those of the templates.

**Class names:** aas_pydantic reads an element back as the class its dump names, among all classes
of the package. A generated class named like another one with other fields gets a name of its own
(`lab_generate.RENAMED`, `READABLE`): `FlowCondition`, `ProcessStepBinding`, `InputBinding`,
`ProcessParameterGroup`; the product's part is a `ProductPart`; the coordinates' classes are `RelativeCoordinate`, `CoordinateX`, ...

## Variables and Coordinates

A module's values and where it is: aas-model's `Variables` submodel
(`submodel_templates/variables.py`), used by the stations and the modules alike. The lab's modules
keep no live value in the AAS: their values are fields of time series (`State/Module`,
`State/<Skill>`, `State/Procedures`, `Measurements/<Item>`), whose rows a mapping writes to the
time series database and whose segment says where they are; a reader asks the database for the
latest value or a span.

```
Variables
├── {variable}                    VariableProp: a live value the mapping feeds; what it shows is its
│                                 supplemental semantic id (a skill's state, a parameter, an input)
├── State                         time series of discrete status (PackML state, occupation)
├── Measurements                  time series of measured values, and:
│   └── Coordinates               where the asset and its points are
│       └── {coordinate}          RelativeCoordinate; its meaning a supplemental semantic id
│           ├── RelativeTo        the coordinate it is relative to, in this AAS or another
│           ├── X, Y, Z           mm, along the parent's axes          (IDTA 02075 x/y/zframe)
│           ├── Roll, Pitch, Yaw  degrees, about the parent's fixed X, then Y, then Z axis
│           └── {value}Source     the variable a moving value is (ZSource)
└── Log                           time series of what is logged (skill calls)
```

| Element | Class | Semantic id |
| --- | --- | --- |
| `Measurements/Coordinates` | `Coordinates` | `https://smartproductionlab.aau.dk/variables/Coordinates/1/0` |
| `.../{coordinate}` | `RelativeCoordinate` | `https://smartproductionlab.aau.dk/variables/Coordinate/1/0` |
| `.../{coordinate}/RelativeTo` | `CoordinateRelativeTo` | `https://smartproductionlab.aau.dk/variables/Coordinate/RelativeTo/1/0` |
| `.../{coordinate}/X`, `Y`, `Z` | `CoordinateX`, `CoordinateY`, `CoordinateZ` | `https://admin-shell.io/idta/cds/xframe/1`, `yframe`, `zframe` (xs:double, mm) |
| `.../{coordinate}/Roll`, `Pitch`, `Yaw` | `CoordinateRoll`, `CoordinatePitch`, `CoordinateYaw` | `https://admin-shell.io/idta/cds/rxframe/1`, `ryframe`, `rzframe` (xs:double, deg) |
| `.../{coordinate}/{value}Source` | `CoordinateSource` | `https://smartproductionlab.aau.dk/variables/Coordinate/Source/1/0` |

- **A tree of transforms across AASs,** rooted at one coordinate without `RelativeTo` (in the lab, the
  planar table's base): a module's base is relative to it, the module's points and mounts to its
  base, an end effector to its mount, a shuttle to the table's base, a product to the shuttle it
  rides. Where a point is in the root's frame is composed along the references (R = Rz(Yaw)
  Ry(Pitch) Rx(Roll), as ROS's RPY), never stored.
- **Measurements,** because the modules will report where they are themselves (RFID): even a fixed
  pose is measured.
- **A part that moves is two coordinates:** a fixed mount, and the moving part relative to it, whose
  moving values are each one variable (`ZSource`). A record of its history is then that variable's.
- **Meanings** come from the lab's vocabulary (`https://smartproductionlab.aau.dk/semantics/...`):
  TableBase, ModuleBase, Mount, EndEffector, Mover, Flyway, TransferPoint, ProcessingPoint,
  PickPoint, PlacePoint.

## Authoring and building

Write an instance with the classes, element by element, and build the AAS:

```python
from aas_model import Product, build_from_model
from aas_model.submodel_templates.product import production_sequence as ps

vial = Product(id_short="Vial2mLAAS", id="https://smartproductionlab.aau.dk/aas/Vial2mLAAS",
               production_sequence=ps.ProductionSequence(...))
store = build_from_model(vial)          # a BaSyx object store: the shell and its submodels
```

The lab's reference instances, written out in full, are in iec61499-mgmt-py: the products
(`cell/examples/products`), the processes (`cell/examples/processes`), and the modules, the line, the
planar table and its shuttles built from their specs by `modreg` (`cell/examples/example_line.py`,
which writes every AAS and can publish them to an AAS server).

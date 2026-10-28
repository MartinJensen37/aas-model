"""The AAS of a product type (ISA-88's general recipe).

- **Nameplate** (IDTA 02006): what the product is.
- **Hierarchical Structures** (IDTA 02011): its bill of material; a part states its quantity.
- **Process Parameters** (IDTA 02031-1 with the lab's extension): the processes the product needs,
  each with the product's values, the materials it uses and the capability it requires.
- **Capability Description** (IDTA 02020, role Required): those capabilities with their values.
- **Production Sequence** (the process sequence planner's): the recipe, its steps in order.

One per product type: an order of many items uses the same one, and a part with a recipe of its own
has one too. The recipe bound to a line is a process AAS (``aas_model.process_template``).
"""

from __future__ import annotations

import base64
from typing import ClassVar, Dict, Optional

from aas_pydantic import AAS, Property
from aas_pydantic.submodel_templates import capability_description as cd
from aas_pydantic.submodel_templates.hierarchical_structures import ArcheType, EntryNode, HierarchicalStructures, Node
from aas_pydantic.submodel_templates.nameplate import ManufacturerProductDesignation, Nameplate
from pydantic import model_validator

from aas_model.constants import BASE_URL
from aas_model.resource_template.modules.submodels import lab_nameplate
from aas_model.submodel_templates.product.process_parameters import Processes, ProcessParameters
from aas_model.submodel_templates.product.production_sequence import ProductionSequence

PLANS = f"{BASE_URL}/sm/process-plan"
QUANTITY = f"{BASE_URL}/semantics/Quantity"
QUANTITY_UNIT = f"{BASE_URL}/semantics/QuantityUnit"


def plan_id(aas_id: str) -> str:
    """The identifier of a product's own Production Sequence: the planner finds the recipe by it."""
    return f"{PLANS}/{base64.urlsafe_b64encode(aas_id.encode()).decode().rstrip('=')}"


class PartQuantity(Property):
    """How much of a part the product holds, in ``QuantityUnit``."""
    id_short: str = "Quantity"
    semantic_id: str = QUANTITY
    value_type: str = "xs:double"


class PartQuantityUnit(Property):
    """The unit of the part's ``Quantity``: piece, mL."""
    id_short: str = "QuantityUnit"
    semantic_id: str = QUANTITY_UNIT


class Part(Node):
    """A part of the product. IDTA 02011 counts parts (BulkCount); a product also holds amounts
    (2 mL of liquid), so a part states its quantity and the unit of it, as the planner writes them.
    A part made by a recipe of its own is a self-managed entity naming its asset."""
    description: str = ""
    entity_type: str = "CoManagedEntity"
    global_asset_id: str = ""
    Quantity: Optional[PartQuantity] = None
    QuantityUnit: Optional[PartQuantityUnit] = None
    Node: Dict[str, "Part"] = {}


class ProductEntry(EntryNode):
    """The product itself, the entry node of its bill of material."""
    description: str = ""
    Node: Dict[str, Part] = {}


class BillOfMaterial(HierarchicalStructures):
    EntryNode: ProductEntry = ProductEntry()


def bill_of_material() -> BillOfMaterial:
    return BillOfMaterial(id_short="HierarchicalStructures", EntryNode=ProductEntry(), ArcheType=ArcheType(value="OneDown"))


def product_nameplate() -> Nameplate:
    plate = lab_nameplate()
    plate.ManufacturerProductDesignation = ManufacturerProductDesignation(value={"en": "Product"})
    return plate


class Product(AAS):
    """AAS of a product type: what it is, what it consists of, the processes it needs and the recipe
    that makes it."""
    model_config = {"extra": "forbid"}
    # A product AAS describes a kind of product, not one item of it.
    ASSET_KIND: ClassVar[str] = "Type"
    asset_type: str = f"{BASE_URL}/Product"
    nameplate: Nameplate = product_nameplate()
    hierarchical_structures: BillOfMaterial = bill_of_material()
    process_parameters: ProcessParameters = ProcessParameters(id_short="ProcessParameters", Processes=Processes())
    capability_description: Optional[cd.CapabilityDescription] = None
    production_sequence: Optional[ProductionSequence] = None

    @model_validator(mode="after")
    def the_recipe_has_the_planners_identifier(self):
        recipe = self.production_sequence
        if recipe is not None and recipe.id == recipe.id_short:          # no identifier given
            recipe.id = plan_id(self.id)
        return self


Part.model_rebuild()
ProductEntry.model_rebuild()
BillOfMaterial.model_rebuild()
Product.model_rebuild()

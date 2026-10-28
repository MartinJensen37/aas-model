"""ProcessInformation - generated from IDTA template.
Source: templates/process/ProcessInformation.json
"""

from __future__ import annotations

from typing import Any, ClassVar, List, TypeAlias
from aas_pydantic import (
    Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)
from aas_pydantic.aas_model import AasIdString

class Product(ReferenceElement):
    id_short: AasIdString = "Product"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/Product/1/0"
    description: str = "The product whose recipe is bound (a model reference to its AAS)."

class Line(ReferenceElement):
    id_short: AasIdString = "Line"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/Line/1/0"
    description: str = "The production system the recipe is bound to (a model reference to its AAS)."

class Recipe(ReferenceElement):
    id_short: AasIdString = "Recipe"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/Recipe/1/0"
    description: str = "The recipe that is bound: the product's Production Sequence submodel."

class RecipeRevision(Property):
    id_short: AasIdString = "RecipeRevision"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/RecipeRevision/1/0"
    description: str = "The revision of the recipe the bindings were made for; a newer recipe needs binding again."
    value_type: str = "xs:nonNegativeInteger"

class Status(Property):
    id_short: AasIdString = "Status"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/Status/1/0"
    description: str = "Where the binding stands: Draft, Approved or Withdrawn."
    value_type: str = "xs:string"

class ProcessInformation(Submodel):
    id_short: AasIdString = "ProcessInformation"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessInformation/1/0/Submodel"
    description: str = "What the process AAS binds: the product, the line and the recipe it binds, and the state of the binding."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    Product: Product_t
    Line: Line_t
    Recipe: Recipe_t
    RecipeRevision: RecipeRevision_t
    Status: Status_t

# alias so field ``Product_t`` can name a class of the same id_short
Product_t: TypeAlias = Product
# alias so field ``Line_t`` can name a class of the same id_short
Line_t: TypeAlias = Line
# alias so field ``Recipe_t`` can name a class of the same id_short
Recipe_t: TypeAlias = Recipe
# alias so field ``RecipeRevision_t`` can name a class of the same id_short
RecipeRevision_t: TypeAlias = RecipeRevision
# alias so field ``Status_t`` can name a class of the same id_short
Status_t: TypeAlias = Status
# ── Resolve forward references (Pydantic circular refs) ──
Product.model_rebuild()
Line.model_rebuild()
Recipe.model_rebuild()
RecipeRevision.model_rebuild()
Status.model_rebuild()
ProcessInformation.model_rebuild()

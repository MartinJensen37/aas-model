"""Validation - generated from IDTA template.
Source: templates/process/Validation.json
"""

from __future__ import annotations

from typing import Any, ClassVar, List, Optional, TypeAlias
from aas_pydantic import (
    Property, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)
from aas_pydantic.aas_model import AasIdString

class Result(Property):
    id_short: AasIdString = "Result"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessValidation/Result/1/0"
    description: str = "Fits, or DoesNotFit."
    value_type: str = "xs:string"

class CheckedBy(Property):
    id_short: AasIdString = "CheckedBy"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessValidation/CheckedBy/1/0"
    description: str = "The check that gave the result."
    value_type: str = "xs:string"

class FindingsItem(Property):
    value_type: str = "xs:string"

class Findings(SubmodelElementList):
    id_short: AasIdString = "Findings"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessValidation/Findings/1/0"
    description: str = "What the check found, one text per finding; empty when the recipe fits."
    type_value_list_element: str = "Property"
    value_type_list_element: str = "xs:string"
    order_relevant: bool = True
    item_type: ClassVar = FindingsItem
    value: List[FindingsItem] = []

class Validation(Submodel):
    id_short: AasIdString = "Validation"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessValidation/1/0/Submodel"
    description: str = "Whether the bound recipe fits the line: the result of the plan check and what it found."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    Result: Result_t
    CheckedBy: CheckedBy_t
    Findings: Optional[Findings_t] = None

# alias so field ``Result_t`` can name a class of the same id_short
Result_t: TypeAlias = Result
# alias so field ``CheckedBy_t`` can name a class of the same id_short
CheckedBy_t: TypeAlias = CheckedBy
# alias so field ``Findings_t`` can name a class of the same id_short
Findings_t: TypeAlias = Findings
# ── Resolve forward references (Pydantic circular refs) ──
Result.model_rebuild()
CheckedBy.model_rebuild()
FindingsItem.model_rebuild()
Findings.model_rebuild()
Validation.model_rebuild()

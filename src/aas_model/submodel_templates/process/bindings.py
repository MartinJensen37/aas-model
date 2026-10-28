"""Bindings - generated from IDTA template.
Source: templates/process/Bindings.json
"""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)
from pydantic import Field
from aas_pydantic.aas_model import AasIdString

class NodeId(Property):
    id_short: AasIdString = "NodeId"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/NodeId/1/0"
    description: str = "The NodeId of the step in the recipe."
    value_type: str = "xs:string"

class BoundStep(ReferenceElement):
    id_short: AasIdString = "Step"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessBindings/Step/1/0"
    description: str = "The step in the product's recipe (Production Sequence)."

class Resource(ReferenceElement):
    id_short: AasIdString = "Resource"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Resource/1/0"
    description: str = "The resource that carries the step out (a model reference to its AAS); none for a manual step."

class BoundSkill(ReferenceElement):
    id_short: AasIdString = "Skill"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Skill/1/0"
    description: str = "The skill of the resource that carries the step out; none for a manual step."

class ExecutionMode(Property):
    id_short: AasIdString = "ExecutionMode"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/ExecutionMode/1/0"
    description: str = "How the step is carried out: station (by a resource's skill) or manual."
    value_type: str = "xs:string"

class Name(Property):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Name/1/0"
    description: str = "The name of the skill's input."
    value_type: str = "xs:string"

class SourceElement(ReferenceElement):
    id_short: AasIdString = "SourceElement"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/SourceElement/1/0"
    description: str = "The product's element whose value the input takes (a process parameter of its Process Parameters)."

class Value(Property):
    id_short: AasIdString = "Value"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Value/1/0"
    description: str = "The constant the input takes, when no SourceElement is given."
    value_type: str = "xs:string"

class InputReference(ReferenceElement):
    id_short: AasIdString = "InputReference"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/InputReference/1/0"
    description: str = "The input itself: a variable of the Operation of the skill's Start command."

class InputBinding(SubmodelElementCollection):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Binding/1/0"
    description: str = "What one input of the skill is handed: a process parameter of the product, or a constant."
    Name: Name_t
    SourceElement: Optional[SourceElement_t] = None
    Value: Optional[Value_t] = None
    InputReference: InputReference_t

class InputBindings(SubmodelElementCollection):
    id_short: AasIdString = "Bindings"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProductionSequence/Bindings/1/0"
    description: str = "What the skill's inputs are handed."
    Binding: Dict[str, Binding_t] = Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class ProcessStepBinding(SubmodelElementCollection):
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessBindings/StepBinding/1/0"
    description: str = "The binding of one step of the recipe, named by the step's NodeId."
    NodeId: NodeId_t
    Step: Step_t
    Resource: Optional[Resource_t] = None
    Skill: Optional[Skill_t] = None
    ExecutionMode: ExecutionMode_t
    Bindings: Optional[InputBindings] = None

class ProcessBindings(Submodel):
    id_short: AasIdString = "Bindings"
    semantic_id: str = "https://smartproductionlab.aau.dk/ProcessBindings/1/0/Submodel"
    description: str = "The recipe bound to the line: per step of the product's recipe, the resource and the skill that carry it out and what each input of the skill is handed."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    StepBinding: Dict[str, StepBinding_t] = {}

# alias so field ``Name_t`` can name a class of the same id_short
Name_t: TypeAlias = Name
# alias so field ``SourceElement_t`` can name a class of the same id_short
SourceElement_t: TypeAlias = SourceElement
# alias so field ``Value_t`` can name a class of the same id_short
Value_t: TypeAlias = Value
# alias so field ``InputReference_t`` can name a class of the same id_short
InputReference_t: TypeAlias = InputReference
# alias so field ``Binding_t`` can name a class of the same id_short
Binding_t: TypeAlias = InputBinding
# alias so field ``NodeId_t`` can name a class of the same id_short
NodeId_t: TypeAlias = NodeId
# alias so field ``Step_t`` can name a class of the same id_short
Step_t: TypeAlias = BoundStep
# alias so field ``Resource_t`` can name a class of the same id_short
Resource_t: TypeAlias = Resource
# alias so field ``Skill_t`` can name a class of the same id_short
Skill_t: TypeAlias = BoundSkill
# alias so field ``ExecutionMode_t`` can name a class of the same id_short
ExecutionMode_t: TypeAlias = ExecutionMode
# alias so field ``StepBinding_t`` can name a class of the same id_short
StepBinding_t: TypeAlias = ProcessStepBinding
# ── Resolve forward references (Pydantic circular refs) ──
NodeId.model_rebuild()
BoundStep.model_rebuild()
Resource.model_rebuild()
BoundSkill.model_rebuild()
ExecutionMode.model_rebuild()
Name.model_rebuild()
SourceElement.model_rebuild()
Value.model_rebuild()
InputReference.model_rebuild()
InputBinding.model_rebuild()
InputBindings.model_rebuild()
ProcessStepBinding.model_rebuild()
ProcessBindings.model_rebuild()

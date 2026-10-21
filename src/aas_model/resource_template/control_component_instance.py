"""CCI extension, reference paths and optional skill authoring utilities.

Built on our extended CCI (``aas_model.submodel_templates.control_component_instance``),
which extends the generated IDTA ControlComponentInstance Skill with:
- an ``interface_reference`` pointing at the skill's NATIVE interface (the AID
  action of whichever interface the asset offers it on),
- an ``operation`` (AAS Operation) whose ``invocationDelegation`` qualifier
  carries the generated DMP operation endpoint,
- an ``Endpoints`` container that holds, per skill, an annotated
  RelationshipElement (``this skill has this native interface``) instead of
  generic endpoint/interface ReferenceElements.

Named-field style: children are DIRECT named fields (no ``value``/``submodel_element``
wrapper); dynamic maps (endpoints/skills) are ``Dict[str, X]`` fields.
"""

from __future__ import annotations

from aas_pydantic import Property
from aas_pydantic import (
    Key, ModelReference, ReferenceElement, Qualifier,
)
from aas_pydantic.submodel_templates.control_component_instance import (
    ControlComponentInstance, Type_instance,
)
from aas_model.constants import INVOCATION_ORIGIN
from aas_model.resource_template.asset_interfaces_description import affordance_ref

from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, ExtendedSkills, SkillOperation,
    SkillInterfaceRelationship, ResourceEndpoints,
)

# ── Reference paths (self-referential — {aas_id} resolved by id_injector) ──
CCI_SUBMODEL_REF = "{aas_id}/submodels/ControlComponentInstance"

# CCI skill path: .../Skills/<name>
_SKILL_PATH = (
    Key(type_="Submodel", value=CCI_SUBMODEL_REF),
    Key(type_="SubmodelElementCollection", value="Skills"),
)


def skill_ref(name: str) -> ModelReference:
    """Reference to the skill SMC inside this CCI submodel."""
    return ModelReference(key=_SKILL_PATH + (
        Key(type_="SubmodelElementCollection", value=name),
    )).model_copy(deep=True)


def _operation_variable(
    name: str, *, value_type: str = "xs:string", description: str = "",
) -> Property:
    v = Property()
    v.id_short = name
    v.value_type = value_type
    if description:
        v.description = description
    return v


def skill_operation(
    name: str, *, synchronous: bool = True, has_response: bool = True,
) -> SkillOperation:
    """The skill's AAS Operation — invoked by clients, delegated to the
    DMP via the ``invocationDelegation`` qualifier.

    The input/inoutput/output variables mirror the native action's
    command / commandResponse payloads (Uuid inout, State output) so
    the operation can also be rendered and manually invoked from the AAS Web
    GUI. The invocation URL's identity segments are finalized by the authoring
    builder using the shared origin and Java-compatible UTF-8 path encoding.

    ``Outcome`` (the FOND branch discriminator) is NOT a default output —
    only actions whose native response actually carries one declare it
    (the process skills; configs author it explicitly). Registration-style
    actions (Occupy/Release) and Halt answer ``State`` only.
    """
    op = SkillOperation(id_short="operation")
    op.qualifiers = [
        Qualifier(
            type_="invocationDelegation",
            value=f"{INVOCATION_ORIGIN}/operations/{{aas_id_short}}/{{skill}}",
            value_type="xs:string",
            kind="ConceptQualifier",
        ),
        Qualifier(
            type_="Synchronous" if synchronous else "Asynchronous",
            value=str(synchronous).lower(),
            # xs:string (not xs:boolean): the aas_pydantic Qualifier value is
            # a str, and basyx's trivial_cast rejects string literals for
            # xs:boolean values.
            value_type="xs:string",
            kind="ConceptQualifier",
        ),
    ]
    op.in_output_variable = [
        _operation_variable("Uuid", description="The UUID of the command"),
    ]
    if has_response:
        op.output_variable = [
            _operation_variable("State", description="The state of the command being executed"),
        ]
    return op


def skill_interface_relationship(name: str, interface: str) -> SkillInterfaceRelationship:
    """Annotated relationship: THIS skill has THIS native interface in the AID.

    ``first`` = the skill SMC in the CCI, ``second`` = the skill's native
    action on ``interface``.  Both use the ``{aas_id}`` macro.
    """
    rel = SkillInterfaceRelationship(id_short=name)
    rel.first = skill_ref(name)
    rel.second = affordance_ref(interface, "actions", name)
    return rel


def extended_skill(
    name: str, interface: str, *,
    synchronous: bool = True,
    has_response: bool = True,
    disabled: bool = False,
) -> ExtendedSkill:
    """Build a standard ExtendedSkill for the CCI.

    Sets the native-interface reference (``interface_reference`` → the AID
    action on ``interface``) and the delegated Operation (``operation``).
    """
    skill = ExtendedSkill(id_short=name)
    skill.Disabled.value = str(disabled).lower()
    skill.interface_reference.value = affordance_ref(interface, "actions", name)
    skill.operation = skill_operation(
        name, synchronous=synchronous, has_response=has_response)
    return skill


class ResourceControlComponentInstance(ControlComponentInstance):
    """CCI variant that uses ExtendedSkills + the per-skill endpoint
    relationships and default-constructs its mandatory children."""
    Endpoints: ResourceEndpoints = ResourceEndpoints()
    Skills: ExtendedSkills = ExtendedSkills()
    Type: Type_instance = Type_instance(
        value=ModelReference(
            key=(Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentType"),)
        )
    )

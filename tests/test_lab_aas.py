"""The lab's AAS types: module, component and production system (ARSO), product and process.
Authored here, exported, restored and built as BaSyx, as a station is."""

from __future__ import annotations

import json

from basyx.aas.adapter.json import json_serialization

from aas_pydantic import Key, ModelReference, Property, Qualifier
from aas_pydantic.convert_util import strip_temp_id_short_attributes
from aas_model import Resource, build_from_model
from aas_model.constants import BASE_URL
from aas_model.process_template import Process
from aas_model.product_template import ProductPart, PartQuantity, PartQuantityUnit, Product, plan_id
from aas_model.resource_template.modules import Component, Module, ModuleSkill, ProductionSystem
from aas_model.submodel_templates.arso import skills as s
from aas_model.submodel_templates.process import bindings as b, process_information as pi, validation as v
from aas_model.submodel_templates.product import production_sequence as ps
from aas_model.submodel_templates.variables import VariableProp

SKILL = f"{BASE_URL}/skill"
MODULE_ID = f"{BASE_URL}/aas/DemoModuleAAS"
PUMP_ID = f"{BASE_URL}/aas/DemoPumpAAS"
PRODUCT_ID = f"{BASE_URL}/aas/DemoVialAAS"
LINE_ID = f"{BASE_URL}/aas/DemoLineAAS"


def reference(*keys: tuple[str, str]) -> ModelReference:
    return ModelReference(key=tuple(Key(type_=t, value=v) for t, v in keys))


def document(model) -> dict:
    store = build_from_model(model)
    strip_temp_id_short_attributes(store)
    return json.loads(json_serialization.object_store_to_json(store))


def submodel(doc: dict, id_short: str) -> dict:
    return next(sm for sm in doc["submodels"] if sm["idShort"] == id_short)


def pump() -> Component:
    """A component with one primitive, Dispense(Volume)."""
    start = s.Start(semantic_id=f"{SKILL}/Start", SkillOperation={"Start": s.SkillOperation(
        id_short="Start", semantic_id=f"{SKILL}/Start",
        input_variable=[Property(id_short="Volume", value_type="xs:double", qualifiers=[
            Qualifier(type_="Unit", value="mL", kind="ConceptQualifier")])],
        output_variable=[Property(id_short="Accepted", value_type="xs:boolean")])})
    component = Component(id_short="DemoPumpAAS", id=PUMP_ID, asset_type=f"{BASE_URL}/Resource/Component/Pump")
    component.skills.Skill["Dispense"] = ModuleSkill(
        id_short="Dispense", supplemental_semantic_ids=[f"{SKILL}/Primitive"],
        SemanticId=s.SemanticId(value=f"{BASE_URL}/skills/Dispense"), Start=start)
    return component


def module() -> Module:
    """A module whose skill Dispensing runs the pump's Dispense, handing down its Volume."""
    own_volume = reference(("Submodel", f"{MODULE_ID}/submodels/Skills"), ("SubmodelElementCollection", "Dispensing"),
                           ("SubmodelElementCollection", "Start"), ("Operation", "Start"), ("Property", "Volume"))
    step = s.SkillStep(
        id_short="Step_0000", NodeId=s.NodeId(value="Dispense"), Kind=s.Kind(value="step"),
        Name=s.Name(value="Dispense"), Order=s.Order(value="0"),
        Skill=s.Skill_production_sequence(value=reference(("Submodel", f"{PUMP_ID}/submodels/Skills"),
                                                          ("SubmodelElementCollection", "Dispense"))),
        Bindings=s.Bindings(StepBinding={"Binding_0000": s.StepBinding(
            id_short="Binding_0000", Name=s.Name(value="Volume"), SourceElement=s.SourceElement(value=own_volume))}))
    start = s.Start(semantic_id=f"{SKILL}/Start", Steps=s.Steps(SkillStep={"Step_0000": step}),
                    SkillOperation={"Start": s.SkillOperation(id_short="Start", semantic_id=f"{SKILL}/Start", input_variable=[
                        Property(id_short="Volume", value_type="xs:double")])})
    made = Module(id_short="DemoModuleAAS", id=MODULE_ID)
    made.skills.Skill["Dispensing"] = ModuleSkill(
        id_short="Dispensing", supplemental_semantic_ids=[f"{SKILL}/Composite"],
        SemanticId=s.SemanticId(value=f"{BASE_URL}/skills/Dispensing"), Start=start)
    made.variables.variable["Weight"] = VariableProp(id_short="Weight", value="0", value_type="xs:double")
    return made


def test_a_module_is_a_resource_with_skills_and_variables():
    made = module()
    assert isinstance(made, Resource)
    doc = document(made)
    assert sorted(sm["idShort"] for sm in doc["submodels"]) == [
        "AssetInterfacesDescription", "AssetInterfacesMappingConfiguration", "HierarchicalStructures",
        "Nameplate", "Skills", "Variables"]
    assert doc["assetAdministrationShells"][0]["assetInformation"]["assetType"] == f"{BASE_URL}/Resource/Module"
    skills = submodel(doc, "Skills")
    assert skills["semanticId"]["keys"][0]["value"] == f"{BASE_URL}/ARSO/Skills/1/0/Submodel"
    dispensing = next(e for e in skills["submodelElements"] if e["idShort"] == "Dispensing")
    assert [r["keys"][0]["value"] for r in dispensing["supplementalSemanticIds"]] == [f"{SKILL}/Composite"]


def test_an_authored_module_reads_back_from_its_json():
    made = module()
    again = Module.model_validate_json(made.model_dump_json())
    assert json.loads(again.model_dump_json()) == json.loads(made.model_dump_json())
    binding = again.skills.Skill["Dispensing"].Start.Steps.SkillStep["Step_0000"].Bindings.StepBinding["Binding_0000"]
    assert isinstance(binding, s.StepBinding) and binding.SourceElement.value.key[-1].value == "Volume"


def test_a_component_holds_its_skills_and_a_system_its_parts():
    assert [sm["idShort"] for sm in document(pump())["submodels"]] == ["Skills"]
    line = ProductionSystem(id_short="DemoLineAAS", id=LINE_ID)
    assert [sm["idShort"] for sm in document(line)["submodels"]] == ["HierarchicalStructures"]


def product() -> Product:
    made = Product(id_short="DemoVialAAS", id=PRODUCT_ID, production_sequence=ps.ProductionSequence(
        id_short="ProductionSequence", PlanSchema=ps.PlanSchema(value="production-sequence/2.0"),
        Revision=ps.Revision(value="1"), SequenceId=ps.SequenceId(value="vial"), Name=ps.Name(value="Vial"),
        Role=ps.Role(value="Primary"), Subject=ps.Subject(value=reference(("AssetAdministrationShell", PRODUCT_ID))),
        Steps=ps.Steps()))
    made.hierarchical_structures.EntryNode.Node["Liquid"] = ProductPart(
        id_short="Liquid", Quantity=PartQuantity(value="2.0"), QuantityUnit=PartQuantityUnit(value="mL"))
    return made


def test_a_product_type_with_its_recipe():
    made = product()
    assert made.production_sequence.id == plan_id(made.id)
    doc = document(made)
    assert doc["assetAdministrationShells"][0]["assetInformation"]["assetKind"] == "Type"
    assert submodel(doc, "ProductionSequence")["id"] == plan_id(made.id)
    again = Product.model_validate_json(made.model_dump_json())
    assert again.hierarchical_structures.EntryNode.Node["Liquid"].Quantity.value == "2.0"


def test_a_process_binds_a_products_recipe_to_a_line():
    made = Process(
        id_short="DemoVialOnDemoLineAAS", id=f"{BASE_URL}/aas/DemoVialOnDemoLineAAS",
        specific_asset_ids={"product": f"{BASE_URL}/assets/DemoVial", "line": f"{BASE_URL}/assets/DemoLine"},
        process_information=pi.ProcessInformation(
            id_short="ProcessInformation",
            Product=pi.Product(value=reference(("AssetAdministrationShell", PRODUCT_ID))),
            Line=pi.Line(value=reference(("AssetAdministrationShell", LINE_ID))),
            Recipe=pi.Recipe(value=reference(("Submodel", plan_id(PRODUCT_ID)))),
            RecipeRevision=pi.RecipeRevision(value="1"), Status=pi.Status(value="Draft")),
        bindings=b.ProcessBindings(id_short="Bindings", StepBinding={"Filling": b.ProcessStepBinding(
            id_short="Filling", NodeId=b.NodeId(value="Filling"),
            Step=b.BoundStep(value=reference(("Submodel", plan_id(PRODUCT_ID)), ("SubmodelElementCollection", "Steps"),
                                        ("SubmodelElementCollection", "Step_0000"))),
            Resource=b.Resource(value=reference(("AssetAdministrationShell", MODULE_ID))),
            Skill=b.BoundSkill(value=reference(("Submodel", f"{MODULE_ID}/submodels/Skills"),
                                          ("SubmodelElementCollection", "Dispensing"))),
            ExecutionMode=b.ExecutionMode(value="station"))}),
        validation=v.Validation(id_short="Validation", Result=v.Result(value="Fits"),
                                CheckedBy=v.CheckedBy(value="plan_check")))
    doc = document(made)
    shell = doc["assetAdministrationShells"][0]
    assert shell["assetInformation"]["assetKind"] == "Type"
    assert sorted(sm["idShort"] for sm in doc["submodels"]) == ["Bindings", "ProcessInformation", "Validation"]
    again = Process.model_validate_json(made.model_dump_json())
    assert again.bindings.StepBinding["Filling"].Skill.value.key[-1].value == "Dispensing"

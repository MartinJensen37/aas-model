"""The lab's own submodel templates (templates/) and the classes generated from them."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lab_generate  # noqa: E402


def test_the_checked_in_classes_are_a_regeneration_of_the_templates(tmp_path):
    made = lab_generate.generate(out=tmp_path)
    checked_in = lab_generate.PACKAGE
    stale = [f"{path.parent.name}/{path.name}" for path in made
             if path.read_text(encoding="utf-8") != (checked_in / path.parent.name / path.name).read_text(encoding="utf-8")]
    assert stale == [], "run: python scripts/lab_generate.py"


@pytest.mark.parametrize("template", sorted(lab_generate.TEMPLATES))
def test_every_template_is_a_template_with_cardinalities(template):
    submodel = json.loads((ROOT / "templates" / template).read_text(encoding="utf-8"))["submodels"][0]
    assert submodel["kind"] == "Template" and submodel["semanticId"]["keys"][0]["value"]

    def elements(element):
        for child in element.get("submodelElements") or (element["value"] if isinstance(element.get("value"), list) else []):
            if "modelType" in child:                        # not the texts of a multi-language value
                yield child
                yield from elements(child)

    missing = [e.get("idShort", e["modelType"]) for e in elements(submodel)
               if not any(q["type"] == "SMT/Cardinality" for q in e.get("qualifiers", []))]
    assert missing == []


def test_a_skill_operation_is_delegated():
    from aas_model.submodel_templates.arso import skills
    from aas_model.submodel_templates.control_component_instance import SkillOperation
    assert issubclass(skills.SkillOperation, SkillOperation)


def test_the_step_bindings_hold_the_inputs_of_the_skill():
    from aas_model.submodel_templates.process import bindings as b
    binding = b.InputBinding(id_short="Binding_0000", Name=b.Name(value="Volume"), InputReference=b.InputReference())
    step = b.ProcessStepBinding(
        id_short="Filling", NodeId=b.NodeId(value="Filling"), Step=b.BoundStep(),
        ExecutionMode=b.ExecutionMode(value="station"),
        Bindings=b.InputBindings(Binding={"Binding_0000": binding}))
    made = b.ProcessBindings(id_short="Bindings", StepBinding={"Filling": step})
    assert made.StepBinding["Filling"].Bindings.Binding["Binding_0000"].Name.value == "Volume"
    assert made.semantic_id == "https://smartproductionlab.aau.dk/ProcessBindings/1/0/Submodel"


def test_every_template_is_described_with_its_current_elements(tmp_path):
    import shutil
    import lab_docs
    copy = tmp_path / "lab-submodels"
    shutil.copytree(lab_docs.DOCS, copy)
    assert {path.name for path in copy.glob("*.md")} == {f"{Path(t).stem}.md" for t in lab_generate.TEMPLATES}
    stale = [path.name for path in lab_docs.write(copy)]
    assert stale == [], "run: python scripts/lab_docs.py"

#!/usr/bin/env python3
"""Regenerate the pydantic models of the lab's own submodel templates.

The templates in ``templates/`` are not IDTA's:

- ``arso/``: the submodels of the resource ontology ARSO (https://w3id.org/2025/arso): Skills,
  Parameters and Control Configuration. They are written from the ontology by ``modreg generate``
  in iec61499-mgmt-py; do not edit them here.
- ``product/``: Process Parameters (IDTA 02031-1 with the lab's extension) and Production Sequence
  (the process sequence planner's recipe).
- ``process/``: the process AAS's Process Information, Bindings and Validation.

``idta_generate.py`` makes their classes as it makes the IDTA ones; this script runs it on each
template, writes the module into the package named in ``TEMPLATES`` and makes three changes to what
the generator wrote (``finished``). Every template and its submodel are described in
``docs/lab-submodels/``.

Run from the repository root::

    python scripts/lab_generate.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import idta_generate  # noqa: E402

PACKAGE = ROOT / "src" / "aas_model" / "submodel_templates"
# Template (relative to templates/) -> the package below PACKAGE it is generated into.
TEMPLATES = {
    "arso/Skills.json": "arso",
    "arso/Parameters.json": "arso",
    "arso/ControlConfiguration.json": "arso",
    "product/ProcessParameters.json": "product",
    "product/ProductionSequence.json": "product",
    "process/ProcessInformation.json": "process",
    "process/Bindings.json": "process",
    "process/Validation.json": "process",
}

# Classes the generator names like classes of another template that has other fields. aas_pydantic
# reads an element back as the class its dump names, so these get names of their own (the idShort
# stays): a skill's flow conditions are not the Production Sequence's.
RENAMED = {"skills": {"Condition": "FlowCondition", "Conditions": "FlowConditions"}}
# Classes the generator names after their semantic id's namespace because the template has another
# element of the same idShort: a readable name instead (these names occur nowhere else).
READABLE = {"bindings": {"Bindings_production_sequence": "InputBindings"}}

ALIAS = re.compile(r"(?:^# alias [^\n]*\n)?^(\w+)_t: TypeAlias = \1\n", re.MULTILINE)
REBUILD = "# ── Resolve forward references"
OPERATION = re.compile(r"^(class \w+)\(Operation\):", re.MULTILINE)
IMPORT = "from aas_pydantic.aas_model import AasIdString\n"
DELEGATED = "from aas_model.submodel_templates.control_component_instance import SkillOperation as DelegatedOperation\n"


def aliases_after_classes(source: str) -> str:
    """A container that holds its own kind (the steps inside a step of a recipe) is named by the
    generator before its class is written. Such a name moves behind the classes, where the
    annotations are resolved."""
    early = [m for m in ALIAS.finditer(source)
             if (cls := re.search(rf"^class {m.group(1)}\(", source, re.MULTILINE)) and cls.start() > m.start()]
    if not early or REBUILD not in source:
        return source
    for m in reversed(early):
        source = source[:m.start()] + source[m.end():]
    return source.replace(REBUILD, "".join(m.group(0) for m in early) + "\n" + REBUILD, 1)


def renamed(source: str, module: str) -> str:
    """The classes of ``RENAMED`` and ``READABLE`` under their own names."""
    for old, new in RENAMED.get(module, {}).items():
        source = re.sub(rf"^class {old}\(", f"class {new}(", source, flags=re.MULTILINE)
        source = re.sub(rf"^{old}_t: TypeAlias = {old}$", f"{old}_t: TypeAlias = {new}", source, flags=re.MULTILINE)
        source = re.sub(rf"^{old}\.model_rebuild\(\)$", f"{new}.model_rebuild()", source, flags=re.MULTILINE)
    for old, new in READABLE.get(module, {}).items():
        source = re.sub(rf"\b{old}\b", new, source)
    return source


def delegated(source: str) -> str:
    """An Operation class derives from ``SkillOperation``: its invocation is delegated to the DMP,
    and its variables are any element (the generator declares them so too)."""
    if OPERATION.search(source):
        source = OPERATION.sub(r"\1(DelegatedOperation):", source)
        source = source.replace(IMPORT, IMPORT + DELEGATED, 1)
    return source


def finished(source: str, module: str) -> str:
    """What the generator wrote, with the three changes, and one line ending on every platform."""
    return delegated(renamed(aliases_after_classes(source.replace("\r\n", "\n")), module)).rstrip() + "\n"


def generate(templates: dict[str, str] = TEMPLATES, out: Path = PACKAGE, root: Path = ROOT) -> list[Path]:
    """Generate every template into its package below ``out``; gives the modules written."""
    made = []
    for template, package in templates.items():
        source = root / "templates" / template
        folder = out / package
        idta_generate.gen_template(str(source), str(folder))
        # The generator names the module after the submodel's idShort.
        id_short = json.loads(source.read_text(encoding="utf-8"))["submodels"][0]["idShort"]
        path = folder / f"{idta_generate.snake(idta_generate.safe_name(id_short))}.py"
        path.write_text(finished(path.read_text(encoding="utf-8"), path.stem), encoding="utf-8", newline="\n")
        made.append(path)
    return made


if __name__ == "__main__":
    os.chdir(ROOT)
    for path in generate():
        print(path.relative_to(ROOT))

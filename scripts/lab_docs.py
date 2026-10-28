#!/usr/bin/env python3
"""Write the element tables of the lab's submodel templates into their descriptions.

Each template in ``templates/`` (see ``lab_generate.TEMPLATES``) is described in
``docs/lab-submodels/<Submodel>.md``: what the submodel is for, how it is used and why it is shaped
so, written by hand, followed by a table of its elements in the form of IDTA's specifications
(idShort, kind, cardinality, semantic id, description). The table is made from the template and
written below the line ``ELEMENTS``; everything above it is left as it is.

Run from the repository root::

    python scripts/lab_docs.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lab_generate import TEMPLATES  # noqa: E402

DOCS = ROOT / "docs" / "lab-submodels"
ELEMENTS = "<!-- The table below is written by scripts/lab_docs.py from the template; do not edit it. -->"
KIND = {"SubmodelElementCollection": "SMC", "SubmodelElementList": "SML", "ReferenceElement": "Ref",
        "RelationshipElement": "Rel", "MultiLanguageProperty": "MLP"}


def cardinality(element: dict) -> str:
    found = next((q["value"] for q in element.get("qualifiers") or [] if q.get("type") == "SMT/Cardinality"), "")
    return {"One": "1", "ZeroToOne": "0..1", "ZeroToMany": "0..*", "OneToMany": "1..*"}.get(found, found)


def text(element: dict) -> str:
    said = " ".join(d["text"] for d in element.get("description") or [] if d.get("language") == "en")
    return " ".join(said.split()).replace("|", "\\|")


def semantic(element: dict) -> str:
    keys = (element.get("semanticId") or {}).get("keys") or []
    return keys[0]["value"] if keys else ""


def code(value: str) -> str:
    return f"`{value}`" if value else "–"


def name(element: dict) -> str:
    """The idShort; one a user names (``Step__00__``) as ``{Step}``."""
    id_short = element.get("idShort", "")
    return f"{{{id_short.split('__')[0]}}}" if "__" in id_short else id_short


def kind(element: dict) -> str:
    made = KIND.get(element["modelType"], element["modelType"])
    if element["modelType"] == "Property":
        made += f" ({element.get('valueType', 'xs:string')})"
    if element["modelType"] == "SubmodelElementList":
        made += f" of {element.get('typeValueListElement', '')}"
    return made


def rows(elements: list[dict], path: str = "", seen: dict | None = None) -> list[str]:
    """One row per element, its children below it. A collection met before with the same content
    (the steps of each command of a skill) is written once; later it points back."""
    seen = {} if seen is None else seen
    made = []
    for element in elements:
        if "modelType" not in element:
            continue
        here = f"{path}/{name(element)}" if path else name(element)
        inside = [c for c in element.get("value") or [] if isinstance(c, dict) and "modelType" in c] \
            if isinstance(element.get("value"), list) else []
        key = json.dumps({k: v for k, v in element.items() if k != "qualifiers"}, sort_keys=True)
        if inside and key in seen:
            made.append(f"| `{here}` | {kind(element)} | {cardinality(element)} | {code(semantic(element))} | "
                        f"As `{seen[key]}`. |")
            continue
        if inside:
            seen[key] = here
        made.append(f"| `{here}` | {kind(element)} | {cardinality(element)} | {code(semantic(element))} | {text(element)} |")
        made += rows(inside, here, seen)
    return made


def table(template: Path) -> str:
    submodel = json.loads(template.read_text(encoding="utf-8"))["submodels"][0]
    version = submodel.get("administration") or {}
    head = [f"**Submodel** `{submodel['idShort']}`, semantic id `{semantic(submodel)}`"
            + (f", version {version.get('version')}.{version.get('revision')}" if version else "")
            + f"; template `templates/{template.relative_to(ROOT / 'templates').as_posix()}`.", "",
            "| Element (path) | Kind | Card. | Semantic id | Description |", "| --- | --- | --- | --- | --- |"]
    return "\n".join([*head, *rows(submodel["submodelElements"])]) + "\n"


def write(docs: Path = DOCS) -> list[Path]:
    """Refresh the table of every description; gives the files that changed. A description that does
    not exist yet is begun with a heading."""
    changed = []
    for template in TEMPLATES:
        source = ROOT / "templates" / template
        stem = Path(template).stem
        path = docs / f"{stem}.md"
        before = path.read_text(encoding="utf-8") if path.exists() else f"# {stem}\n\n"
        above = before.split(ELEMENTS)[0].rstrip() + "\n\n"
        after = f"{above}## Elements\n\n{ELEMENTS}\n\n{table(source)}" if "## Elements" not in above \
            else f"{above}{ELEMENTS}\n\n{table(source)}"
        if after != before:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(after, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


if __name__ == "__main__":
    os.chdir(ROOT)
    for path in write():
        print(path.relative_to(ROOT))

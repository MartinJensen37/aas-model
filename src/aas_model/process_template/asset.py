"""The AAS of a process: a product's recipe bound to one production system (ISA-88's master recipe).

- **Process Information**: the product, the line and the recipe it binds, with the recipe's
  revision and the binding's status.
- **Bindings**: per step of the recipe, the resource and the skill that carry it out and what each
  input of the skill is handed.
- **Validation**: whether the bound recipe fits the line, and what the check found.

Why apart from the product AAS: a reconfiguration of the line changes the resources and at most the
process AAS, never the product; one product on two lines is two process AASs and one product AAS;
the product designer, the line engineer and the vendor each own one AAS. The asset is the process; it
carries the product's and the line's asset ids as specific asset ids, so it is found from either.
"""

from __future__ import annotations

from typing import ClassVar

from aas_pydantic import AAS

from aas_model.constants import BASE_URL
from aas_model.submodel_templates.process.bindings import ProcessBindings
from aas_model.submodel_templates.process.process_information import ProcessInformation
from aas_model.submodel_templates.process.validation import Validation


class Process(AAS):
    """AAS of a process: a product's recipe bound to a production system."""
    model_config = {"extra": "forbid"}
    # It describes how a kind of product is made on a line, not one run.
    ASSET_KIND: ClassVar[str] = "Type"
    asset_type: str = f"{BASE_URL}/Process"
    process_information: ProcessInformation
    bindings: ProcessBindings
    validation: Validation

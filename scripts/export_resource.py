#!/usr/bin/env python3
"""Export a Python-authored Resource as the JSON the registration service loads.

The registration service validates the export as a plain ``Resource`` and
builds the AAS from it, so a factory may return a subclass only if the export
loads as a ``Resource`` without loss: a subclass that adds fields is rejected.
Run from the aas-model root::

    PYTHONPATH=src python scripts/export_resource.py
    PYTHONPATH=src python scripts/export_resource.py my_package.resources:station
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from pydantic import ValidationError

from aas_model import Resource


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "factory",
        nargs="?",
        default="aas_model.resource_instances.stopperingModule:syntegon_stoppering",
        help="Python module:factory returning a Resource model",
    )
    args = parser.parse_args()

    module_name, separator, factory_name = args.factory.partition(":")
    if not separator or not module_name or not factory_name:
        parser.error("factory must use module:factory syntax")
    resource = getattr(importlib.import_module(module_name), factory_name)()
    if not isinstance(resource, Resource):
        parser.error("factory must return a Resource model")
    export = resource.model_dump_json(indent=2)
    try:
        loaded = Resource.model_validate_json(export)
    except ValidationError as error:
        parser.error(f"factory must return a Resource model the registration service can load: {error}")
    if json.loads(loaded.model_dump_json()) != json.loads(export):
        parser.error("factory must return a Resource model the registration service can load without loss")
    sys.stdout.write(export)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

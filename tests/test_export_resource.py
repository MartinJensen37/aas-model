"""The Resource export the registration service loads (scripts/export_resource.py)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import ModuleType

import pytest

from aas_model import Resource
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.resource_instances.stopperingModule import syntegon_stoppering
from aas_pydantic import Property, Submodel

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_resource.py"


@pytest.mark.parametrize("explicit_factory", [False, True])
def test_export_dumps_a_python_resource(explicit_factory):
    command = [sys.executable, str(SCRIPT)]
    if explicit_factory:
        command.append("aas_model.resource_instances.stopperingModule:syntegon_stoppering")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)

    assert json.loads(result.stdout) == json.loads(syntegon_stoppering().model_dump_json())


@pytest.mark.parametrize("name", sorted(RESOURCE_FACTORIES))
def test_every_resource_loads_as_a_resource_without_loss(name):
    export = RESOURCE_FACTORIES[name]().model_dump_json()

    assert json.loads(Resource.model_validate_json(export).model_dump_json()) == json.loads(export)


def test_export_rejects_subclass_fields_the_service_cannot_load(monkeypatch, capsys):
    class Diagnostics(Submodel):
        status: Property = Property(value="READY")

    class Instrument(Resource):
        diagnostics: Diagnostics

    module = ModuleType("custom_resource_factory")
    module.station = lambda: Instrument(
        id_short="Instrument", diagnostics=Diagnostics(id_short="Diagnostics"),
    )
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(sys, "argv", ["export_resource.py", "custom_resource_factory:station"])
    script = runpy.run_path(str(SCRIPT))

    with pytest.raises(SystemExit) as error:
        script["main"]()

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert "the registration service can load" in captured.err

"""Coordinates in Variables/Measurements: authored, exported, restored and built as BaSyx."""

from __future__ import annotations

import json

from basyx.aas.adapter.json import AASToJsonEncoder

from aas_pydantic import Key, ModelReference
from aas_model import Resource, build_from_model
from aas_model._serde import parse_submodel_dict
from aas_model.submodel_templates.coordinates import (
    CoordinateRelativeTo, CoordinateSource, Coordinates, CoordinateX, CoordinateY, CoordinateYaw, CoordinateZ,
    RelativeCoordinate, VAR_COORDINATE,
)
from aas_model.submodel_templates.variables import MeasurementsGroup, VariableProp, Variables

TRANSFER_POINT = "https://smartproductionlab.aau.dk/semantics/TransferPoint"


def _variables() -> Variables:
    base = ModelReference(key=(
        Key(type_="Submodel", value="{aas_id}/submodels/Variables"),
        Key(type_="SubmodelElementCollection", value="Measurements"),
        Key(type_="SubmodelElementCollection", value="Coordinates"),
        Key(type_="SubmodelElementCollection", value="ModuleBase"),
    ))
    position = ModelReference(key=(
        Key(type_="Submodel", value="{aas_id}/submodels/Variables"),
        Key(type_="Property", value="LinearAxis_ActualPosition"),
    ))
    return Variables(
        id_short="Variables",
        variable={"LinearAxis_ActualPosition": VariableProp(id_short="LinearAxis_ActualPosition", value="0", value_type="xs:double")},
        Measurements=MeasurementsGroup(value={"Coordinates": Coordinates(coordinate={
            "ModuleBase": RelativeCoordinate(id_short="ModuleBase", X=CoordinateX(value="240.0"), Y=CoordinateY(value="720.0"), Yaw=CoordinateYaw(value="180.0")),
            "Transfer": RelativeCoordinate(id_short="Transfer", supplemental_semantic_ids=[TRANSFER_POINT],
                                   RelativeTo=CoordinateRelativeTo(value=base), Y=CoordinateY(value="60.0")),
            "LinearAxis": RelativeCoordinate(id_short="LinearAxis", RelativeTo=CoordinateRelativeTo(value=base), Z=CoordinateZ(value="40.0"),
                                     source={"ZSource": CoordinateSource(id_short="ZSource", value=position)}),
        })}),
    )


def _published() -> dict:
    asset = Resource(id_short="coordinatesTestAAS", variables=_variables())
    restored = Resource.model_validate_json(asset.model_dump_json())
    submodel = {s.id_short: s for s in build_from_model(restored)}["Variables"]
    return json.loads(json.dumps(submodel, cls=AASToJsonEncoder))


def _at(element: dict, *path: str) -> dict:
    for step in path:
        element = next(c for c in element.get("submodelElements") or element["value"] if c["idShort"] == step)
    return element


def test_a_coordinate_is_a_pose_relative_to_another():
    transfer = _at(_published(), "Measurements", "Coordinates", "Transfer")
    assert transfer["semanticId"]["keys"][0]["value"] == VAR_COORDINATE
    assert transfer["supplementalSemanticIds"][0]["keys"][0]["value"] == TRANSFER_POINT
    assert [e["idShort"] for e in transfer["value"]] == ["RelativeTo", "X", "Y", "Z", "Roll", "Pitch", "Yaw"]
    assert _at(transfer, "Y")["value"] == "60.0" and _at(transfer, "X")["value"] == "0.0"
    assert _at(transfer, "Yaw")["qualifiers"][0]["value"] == "deg"
    parent = _at(transfer, "RelativeTo")["value"]["keys"]
    assert parent[0]["value"] == "https://smartproductionlab.aau.dk/aas/coordinatesTestAAS/submodels/Variables"
    assert parent[-1]["value"] == "ModuleBase"


def test_a_moving_value_names_the_variable_it_is():
    axis = _at(_published(), "Measurements", "Coordinates", "LinearAxis")
    assert _at(axis, "ZSource")["value"]["keys"][-1]["value"] == "LinearAxis_ActualPosition"


def test_the_coordinates_parse_back_into_the_model():
    parsed = parse_submodel_dict(_published(), Variables)
    coordinates = parsed.Measurements.value["Coordinates"]
    assert isinstance(coordinates, Coordinates)
    assert coordinates.coordinate["ModuleBase"].Yaw.value in ("180.0", 180.0)
    assert coordinates.coordinate["LinearAxis"].source["ZSource"].value.key[-1].value == "LinearAxis_ActualPosition"

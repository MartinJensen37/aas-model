"""Coordinates — where an asset and its points are, in ``Variables/Measurements/Coordinates``.

Each coordinate is a pose relative to another coordinate, named by reference, in this AAS or in
another. Together the references form a tree of transforms (as ROS's tf tree), rooted at one
coordinate that names no parent: in the lab, the planar table's base. Where a point is in the root's
frame is composed along the references; it is never stored.

Structure::

    Measurements
    └── Coordinates
        └── <coordinate>[]           Coordinate (its meaning as a supplemental semantic id:
            │                         TableBase, ModuleBase, Mount, EndEffector, Mover,
            │                         TransferPoint, ...)
            ├── RelativeTo           the parent coordinate (absent: the root, or not placed yet)
            ├── X, Y, Z              mm, along the parent's axes          (IDTA 02075 x/y/zframe)
            ├── Roll, Pitch, Yaw     degrees, about the parent's fixed X, then Y, then Z axis:
            │                         R = Rz(Yaw)·Ry(Pitch)·Rx(Roll)       (IDTA 02075 rx/ry/rzframe)
            └── <value>Source[]      the variable a moving value is (``ZSource`` → the axis'
                                      actual position)

The coordinates are measurements: the modules will report where they are themselves (RFID), so
even a fixed pose is measured. A part that moves is two coordinates: a fixed mount, and the moving
part relative to it, whose moving values are each one variable (``<value>Source``). A product on a
shuttle is relative to the shuttle; a handover changes its ``RelativeTo``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from aas_pydantic import Property, Qualifier, ReferenceElement, SubmodelElementCollection
from aas_pydantic.aas_model import AasIdString

from aas_model.constants import BASE_URL

# The classes are named apart from the idShorts (``CoordinateX`` is ``X``): aas_pydantic reads an
# element back as the class its dump names, among all classes of the package.

VAR_COORDINATES = f"{BASE_URL}/variables/Coordinates/1/0"
VAR_COORDINATE = f"{BASE_URL}/variables/Coordinate/1/0"
VAR_RELATIVE_TO = f"{BASE_URL}/variables/Coordinate/RelativeTo/1/0"
VAR_COORDINATE_SOURCE = f"{BASE_URL}/variables/Coordinate/Source/1/0"

# IDTA 02075 (Common Data Specification for frames): the six values of a frame.
XFRAME = "https://admin-shell.io/idta/cds/xframe/1"
YFRAME = "https://admin-shell.io/idta/cds/yframe/1"
ZFRAME = "https://admin-shell.io/idta/cds/zframe/1"
RXFRAME = "https://admin-shell.io/idta/cds/rxframe/1"
RYFRAME = "https://admin-shell.io/idta/cds/ryframe/1"
RZFRAME = "https://admin-shell.io/idta/cds/rzframe/1"


class CoordinateRelativeTo(ReferenceElement):
    """The coordinate this one is relative to: a ModelReference to its Coordinate SMC."""
    id_short: AasIdString = "RelativeTo"
    semantic_id: str = VAR_RELATIVE_TO
    description: str = "The coordinate this one is relative to (a ModelReference to its SMC, in this AAS or another)."


class CoordinateX(Property):
    id_short: AasIdString = "X"
    semantic_id: str = XFRAME
    description: str = "The translation along the parent's X axis, in mm."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="mm", kind="ConceptQualifier")]


class CoordinateY(Property):
    id_short: AasIdString = "Y"
    semantic_id: str = YFRAME
    description: str = "The translation along the parent's Y axis, in mm."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="mm", kind="ConceptQualifier")]


class CoordinateZ(Property):
    id_short: AasIdString = "Z"
    semantic_id: str = ZFRAME
    description: str = "The translation along the parent's Z axis, in mm."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="mm", kind="ConceptQualifier")]


class CoordinateRoll(Property):
    id_short: AasIdString = "Roll"
    semantic_id: str = RXFRAME
    description: str = "The rotation about the parent's X axis, applied first, in degrees."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="deg", kind="ConceptQualifier")]


class CoordinatePitch(Property):
    id_short: AasIdString = "Pitch"
    semantic_id: str = RYFRAME
    description: str = "The rotation about the parent's Y axis, applied second, in degrees."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="deg", kind="ConceptQualifier")]


class CoordinateYaw(Property):
    id_short: AasIdString = "Yaw"
    semantic_id: str = RZFRAME
    description: str = "The rotation about the parent's Z axis, applied last, in degrees."
    value_type: str = "xs:double"
    value: str = "0.0"
    qualifiers: List[Qualifier] = [Qualifier(type_="Unit", value="deg", kind="ConceptQualifier")]


class CoordinateSource(ReferenceElement):
    """The variable a moving value of the coordinate is (``ZSource``: the axis' actual position).
    Its idShort is the value's, followed by ``Source``."""
    semantic_id: str = VAR_COORDINATE_SOURCE
    description: str = "The variable whose value this value of the coordinate is."



class RelativeCoordinate(SubmodelElementCollection):
    """A pose relative to the coordinate ``RelativeTo`` names. What it is (a module's base, a
    transfer point) is its supplemental semantic id, a meaning of the lab's vocabulary."""
    semantic_id: str = VAR_COORDINATE
    description: str = ("A pose relative to the coordinate RelativeTo names: X, Y, Z in mm and Roll, "
                        "Pitch, Yaw in degrees about the parent's fixed X, then Y, then Z axis.")
    RelativeTo: Optional[CoordinateRelativeTo] = None
    X: CoordinateX = CoordinateX()
    Y: CoordinateY = CoordinateY()
    Z: CoordinateZ = CoordinateZ()
    Roll: CoordinateRoll = CoordinateRoll()
    Pitch: CoordinatePitch = CoordinatePitch()
    Yaw: CoordinateYaw = CoordinateYaw()
    # Keys are ``<value>Source`` (``ZSource``).
    source: Dict[str, CoordinateSource] = {}


class Coordinates(SubmodelElementCollection):
    """The coordinates of the asset: its base, its mounts and end effectors, its points."""
    id_short: AasIdString = "Coordinates"
    semantic_id: str = VAR_COORDINATES
    description: str = "Where the asset and its points are: one coordinate each, relative to another by reference."
    coordinate: Dict[str, RelativeCoordinate] = {}

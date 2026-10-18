"""Concrete resource factories; every call returns a newly authored instance."""

from .software import orchestrator, production_planner
from .stations import (
    cytiva_capping, ima_dispensing, ima_loading, omron_camera,
    optima_unloading, syntegon_stoppering,
)
from .systems import aau_filling_line, planar_table
from .transport import planar_shuttle_1, planar_shuttle_2, planar_shuttle_3


RESOURCE_FACTORIES = {
    "syntegonStoppering": syntegon_stoppering,
    "cytivaCapping": cytiva_capping,
    "imaDispensing": ima_dispensing,
    "imaLoadingSystem": ima_loading,
    "optimaUnloading": optima_unloading,
    "omronCamera": omron_camera,
    "planarShuttle1": planar_shuttle_1,
    "planarShuttle2": planar_shuttle_2,
    "planarShuttle3": planar_shuttle_3,
    "planarTable": planar_table,
    "orchestrator": orchestrator,
    "productionPlanner": production_planner,
    "aauFillingLine": aau_filling_line,
}

__all__ = [
    "syntegon_stoppering", "cytiva_capping", "ima_dispensing", "ima_loading",
    "optima_unloading", "omron_camera", "planar_shuttle_1", "planar_shuttle_2",
    "planar_shuttle_3", "planar_table", "orchestrator", "production_planner",
    "aau_filling_line", "RESOURCE_FACTORIES",
]

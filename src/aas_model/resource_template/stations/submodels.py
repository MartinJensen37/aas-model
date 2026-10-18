"""Pydantic capability declarations inherited by domain-specific stations."""

from aas_pydantic import Capability
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilityDescription, CapabilitySet as CapabilitySetType,
)
from aas_model.constants import CSSX


class StopperingCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Processing": CapabilitySetType(id_short="Processing", CapabilityContainer={
            "Stoppering": CapabilityContainer(id_short="Stoppering", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Stoppering",
            )),
        }),
    }


class CappingCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Processing": CapabilitySetType(id_short="Processing", CapabilityContainer={
            "Capping": CapabilityContainer(id_short="Capping", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Capping",
            )),
        }),
    }


class DispensingCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Processing": CapabilitySetType(id_short="Processing", CapabilityContainer={
            "Dispensing": CapabilityContainer(id_short="Dispensing", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Dispensing",
            )),
        }),
    }


class LoadingCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Handling": CapabilitySetType(id_short="Handling", CapabilityContainer={
            "Loading": CapabilityContainer(id_short="Loading", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Loading",
            )),
        }),
    }


class UnloadingCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Handling": CapabilitySetType(id_short="Handling", CapabilityContainer={
            "Unloading": CapabilityContainer(id_short="Unloading", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Unloading",
            )),
            "Scrap": CapabilityContainer(id_short="Scrap", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Scrap",
            )),
        }),
    }


class InspectionCapabilities(CapabilityDescription):
    CapabilitySet: dict[str, CapabilitySetType] = {
        "Inspection": CapabilitySetType(id_short="Inspection", CapabilityContainer={
            "Capture": CapabilityContainer(id_short="Capture", Capability=Capability(
                id_short="Capability", semantic_id=f"{CSSX}#Capture",
            )),
        }),
    }

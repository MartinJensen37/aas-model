"""Python-authored Stoppering module.

Describes the MQTT process skill alongside the shared Resource defaults,
without importing or depending on an external JSON config. The factory
returns a fresh instance so callers can customize it independently.
"""

from aas_pydantic.submodel_templates.nameplate import (
    ManufacturerProductType,
    SerialNumber,
)

from aas_model.constants import BASE_URL, BROKER, SITE, CSSX
from aas_model.resource_template import *
from aas_model.resource_template._helpers import put
from aas_model.submodel_templates.control_component_instance import OperationVariableProp


def syntegon_stoppering() -> Resource:
    """An MQTT Stoppering resource, authored entirely as typed Python objects."""
    plate = nameplate()
    plate.ManufacturerName.value = {"en": "Syntegon Technology GmbH"}
    plate.ManufacturerProductDesignation.value = {"en": "Stoppering System 2024"}
    plate.ManufacturerProductType = ManufacturerProductType(
        value="Pharmaceutical Stoppering Station",
    )
    plate.SerialNumber = SerialNumber(value="SYN-SS-2024-001")
    plate.YearOfConstruction.value = "2024"
    plate.CountryOfOrigin.value = "DE"
    plate.OrderCodeOfManufacturer.value = "SYN-SS-2024-001"

    aid = asset_interfaces_description()
    mqtt = aid.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Syntegon Stoppering System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Stoppering"
    put(mqtt.InteractionMetadata.actions.property_name, "Stoppering", mqtt_action(
        "Stoppering", synchronous=False,
    ))

    cci = control_component_instance()
    skill = extended_skill("Stoppering", synchronous=False)
    skill.operation.output_variable.append(OperationVariableProp(
        id_short="Outcome", description="The outcome of the Stoppering process",
    ))
    put(cci.Skills.Skill, "Stoppering", skill)
    put(cci.Endpoints.Endpoint, "Stoppering", skill_interface_relationship("Stoppering"))

    aimc = asset_interfaces_mapping_configuration()
    aimc.MappingConfigurations.value.append(
        skill_operation_mapping_configuration("Stoppering"),
    )

    return Resource(
        id_short="syntegonStopperingSystemAAS",
        id=f"{BASE_URL}/aas/syntegonStopperingSystemAAS",
        asset_type=f"{CSSX}#StopperingSystem",
        derived_from=f"{BASE_URL}/aas/templates/resource",
        specific_asset_ids={"serialNumber": "SYN-SS-2024-001"},
        nameplate=plate,
        asset_interfaces_description=aid,
        control_component_instance=cci,
        asset_interfaces_mapping_configuration=aimc,
    )

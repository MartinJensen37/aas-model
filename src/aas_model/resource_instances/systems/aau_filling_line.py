"""AAU filling line instance."""

from aas_model.constants import BASE_URL, CSSX
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic import ExternalReference, Key
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, EntryNode, HasPart, HierarchicalStructures, Node,
)
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, SerialNumber,
    YearOfConstruction, CountryOfOrigin,
)
from aas_model.resource_template.systems import CompositeResource


def aau_filling_line() -> CompositeResource:
    identity = "aauFillingLineAAS"
    serial = "AAU-FL-2024-001"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "syntegonStopperingSystemAAS", "cytivaCappingSystemAAS",
        "imaDispensingSystemAAS", "imaLoadingSystemAAS",
        "optimaUnloadingSystemAAS", "omronCameraSystemAAS", "planarTableAAS",
    )
    return CompositeResource(
        id_short=identity, id=resource_id, asset_type=f"{CSSX}#FillingLine",
        specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Filling Line"}),
            ManufacturerProductType=ManufacturerProductType(value="AAU Filling Line"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=serial),
            SerialNumber=SerialNumber(value=serial), YearOfConstruction=YearOfConstruction(value="2024"),
            CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneDown"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={child: Node(id_short=child, global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
                HasPart={f"HasPart_{child}": HasPart(
                    id_short=f"HasPart_{child}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{child}"),)),
                ) for child in children},
            ),
        ),
    )

"""Three explicitly authored planar movers sharing the PlanarShuttle type."""

from aas_pydantic import ExternalReference, Key
from aas_pydantic.submodel_templates.hierarchical_structures import (
    ArcheType, EntryNode, HierarchicalStructures, IsPartOf, Node,
)
from aas_pydantic.submodel_templates.nameplate import (
    Nameplate, URIOfTheProduct, ManufacturerName, ManufacturerProductDesignation,
    ManufacturerProductType, OrderCodeOfManufacturer, YearOfConstruction,
    CountryOfOrigin,
)

from aas_model.constants import BASE_URL, BROKER, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_model.resource_template.transport import PlanarShuttle


def planar_shuttle_1() -> PlanarShuttle:
    identity = "planarTableShuttle1AAS"
    parent = "planarTableAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    # The legacy shuttles shared one serial; their individual serials are unknown.
    resource = PlanarShuttle(
        id_short=identity, id=resource_id,
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Shuttle"}),
            ManufacturerProductType=ManufacturerProductType(value="Planar Motors Shuttle"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=""),
            YearOfConstruction=YearOfConstruction(value="2024"), CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneUp"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={parent: Node(id_short=parent, global_asset_id=f"{BASE_URL}/aas/{parent}")},
                IsPartOf={f"PartOf_{parent}": IsPartOf(
                    id_short=f"PartOf_{parent}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{parent}"),)),
                )},
            ),
        ),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Planar Motors Shuttle"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/Xbot1/"
    return resource


def planar_shuttle_2() -> PlanarShuttle:
    identity = "planarTableShuttle2AAS"
    parent = "planarTableAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = PlanarShuttle(
        id_short=identity, id=resource_id,
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Shuttle"}),
            ManufacturerProductType=ManufacturerProductType(value="Planar Motors Shuttle"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=""),
            YearOfConstruction=YearOfConstruction(value="2024"), CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneUp"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={parent: Node(id_short=parent, global_asset_id=f"{BASE_URL}/aas/{parent}")},
                IsPartOf={f"PartOf_{parent}": IsPartOf(
                    id_short=f"PartOf_{parent}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{parent}"),)),
                )},
            ),
        ),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Planar Motors Shuttle"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/Xbot2/"
    resource.parameters.parameter["Location"].x.parameter.value = 240.0
    return resource


def planar_shuttle_3() -> PlanarShuttle:
    identity = "planarTableShuttle3AAS"
    parent = "planarTableAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = PlanarShuttle(
        id_short=identity, id=resource_id,
        nameplate=Nameplate(
            id_short="Nameplate", URIOfTheProduct=URIOfTheProduct(value=resource_id),
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Shuttle"}),
            ManufacturerProductType=ManufacturerProductType(value="Planar Motors Shuttle"),
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=OrderCodeOfManufacturer(value=""),
            YearOfConstruction=YearOfConstruction(value="2024"), CountryOfOrigin=CountryOfOrigin(value="DK"),
        ),
        hierarchical_structures=HierarchicalStructures(
            id_short="HierarchicalStructures", ArcheType=ArcheType(value="OneUp"),
            EntryNode=EntryNode(
                id_short="EntryNode", global_asset_id=resource_id,
                Node={parent: Node(id_short=parent, global_asset_id=f"{BASE_URL}/aas/{parent}")},
                IsPartOf={f"PartOf_{parent}": IsPartOf(
                    id_short=f"PartOf_{parent}",
                    first=ExternalReference(key=(Key(type_="GlobalReference", value=resource_id),)),
                    second=ExternalReference(key=(Key(type_="GlobalReference", value=f"{BASE_URL}/aas/{parent}"),)),
                )},
            ),
        ),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Planar Motors Shuttle"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/Xbot3/"
    resource.parameters.parameter["Location"].x.parameter.value = 480.0
    return resource

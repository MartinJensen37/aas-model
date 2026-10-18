"""Shared site address; resource identity and topology remain instance-owned."""

from aas_pydantic.submodel_templates.nameplate import (
    AddressInformation, CityTown, NationalCode, Street, Zipcode,
)


SITE_ADDRESS = AddressInformation(
    Street=Street(value={"en": "Fibigerstr\u00e6de 14"}),
    Zipcode=Zipcode(value={"en": "9220"}),
    CityTown=CityTown(value={"en": "Aalborg \u00d8st"}),
    NationalCode=NationalCode(value={"en": "DK"}),
)

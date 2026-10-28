"""The AAS of a product type and its recipe (``docs/lab-aas.md``)."""

from .asset import (
    PLANS, BillOfMaterial, Part, PartQuantity, PartQuantityUnit, Product, ProductEntry, bill_of_material,
    plan_id, product_nameplate,
)

__all__ = ["PLANS", "BillOfMaterial", "Part", "PartQuantity", "PartQuantityUnit", "Product", "ProductEntry",
           "bill_of_material", "plan_id", "product_nameplate"]

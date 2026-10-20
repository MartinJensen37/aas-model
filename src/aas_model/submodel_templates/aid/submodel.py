"""The AID submodel: one dict of interfaces per protocol binding."""

from __future__ import annotations

from typing import Dict

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    AssetInterfacesDescription as _BaseAID,
)

from aas_model.submodel_templates.aid.bindings.bacnet import DmpBacnetInterface
from aas_model.submodel_templates.aid.bindings.can import DmpCanInterface
from aas_model.submodel_templates.aid.bindings.http import DmpHttpInterface
from aas_model.submodel_templates.aid.bindings.iolink import DmpIolinkInterface
from aas_model.submodel_templates.aid.bindings.modbus import DmpModbusInterface
from aas_model.submodel_templates.aid.bindings.mqtt import MqttInterface
from aas_model.submodel_templates.aid.bindings.opcua import DmpOpcuaInterface
from aas_model.submodel_templates.aid.bindings.snmp import DmpSnmpInterface


class DmpAssetInterfacesDescription(_BaseAID):
    """DMP-extended Asset Interfaces Description.

    Every interface lives in its protocol family's ``InterfaceTemplateFor*``
    dict, keyed by its idShort (by convention ``interface_<protocol>``, e.g.
    ``InterfaceTemplateForOPCUA["interface_opcua"]``). No protocol is a
    default: an asset describes exactly the interfaces it has. The interface
    families share the ``…/Interface`` semanticId; the parser tells them
    apart by their protocol-binding supplemental IRI.
    """
    InterfaceTemplateForHTTP: Dict[str, DmpHttpInterface] = {}
    InterfaceTemplateForMODBUS: Dict[str, DmpModbusInterface] = {}
    InterfaceTemplateForMQTT: Dict[str, MqttInterface] = {}
    InterfaceTemplateForOPCUA: Dict[str, DmpOpcuaInterface] = {}
    InterfaceTemplateForBacnet: Dict[str, DmpBacnetInterface] = {}
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST: Dict[str, DmpIolinkInterface] = {}
    InterfaceTemplateForSNMP: Dict[str, DmpSnmpInterface] = {}
    InterfaceTemplateForCAN: Dict[str, DmpCanInterface] = {}

"""Common software-resource template, without application-specific operations."""

from aas_model.constants import CSSX
from aas_model.resource_template.asset import Resource
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.resource_template.operational import MqttInterfaces


class SoftwareResource(Resource):
    asset_type: str = f"{CSSX}#SoftwareResource"


class MqttSoftwareResource(SoftwareResource):
    """Software exposes MQTT without inheriting station-specific skills."""

    asset_interfaces_description: DmpAssetInterfacesDescription = MqttInterfaces(
        id_short="AssetInterfacesDescription",
    )

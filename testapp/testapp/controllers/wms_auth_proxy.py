from mapfish.controllers.auth_proxy import AuthProxyController
from mapfish.controllers.auth_proxy import WMSLayer, TileCacheLayer
from mapfish.controllers.security import Deny

from authkit.permissions import HasAuthKitRole, ValidAuthKitUser
from authkit.authorize.pylons_adaptors import authorized

from testapp.lib.base import *

import logging
log = logging.getLogger(__name__)

def get_permissions():
    return WmsAuthProxyController()._get_permissions()

class WmsAuthProxyController(AuthProxyController):
    # FIXME: tests want to access the index method and fail if missing.
    # Don't know where this is coming from.
    def index(self):
        return ""

    def __init__(self):
        layers = []

        # Configuration:
        #
        # Users
        #  alice: rolealice, editor
        #  bob: rolebob, admin
        #  carol: -
        
        # WMS sublayers:
        #  parkings
        #  summits
        #  background

        WMS_SERVER = "http://localhost:9999"

        layers.append(WMSLayer(alias="no_restrictions",
                               url=WMS_SERVER,
                               layers={}))

        layers.append(WMSLayer(alias="default_deny",
                               url=WMS_SERVER,
                               layers={
                                   "parkings": HasAuthKitRole('rolealice'),
                                   "DEFAULT": Deny()
                               }))

        layers.append(WMSLayer(alias="default_allow",
                               url=WMS_SERVER,
                               layers={
                                   "parkings": HasAuthKitRole('rolealice')
                               }))

        layers.append(WMSLayer(alias="wms0",
                               url=WMS_SERVER,
                               layers={
                                   # background is public
                                   "parkings": HasAuthKitRole('editor'),
                                   "summits": HasAuthKitRole(['editor', 'admin'], all=True)
                               }))

        # TODO: test tilecache layer

        self.set_layers(layers)

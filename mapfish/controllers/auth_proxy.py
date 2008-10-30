from pylons import request, response
from pylons.decorators import jsonify 
from pylons.controllers import WSGIController

from authkit.authorize.pylons_adaptors import authorized
from authkit.authorize import NotAuthorizedError
import re
import cgi
import urlparse
import urllib2
from urllib import urlencode

def add_routes(map, url, controller):
    """Add the pylons routes for a proxy
    """
    map.connect(url + "*more", controller=controller, action='get',
                conditions=dict(method=['GET']))

class Layer(object):
    def __init__(self, alias, url, layers, **kwargs):
        self.alias = alias
        self.url = url
        self.layers = layers
        self.options = kwargs

    def get_permissions(self):
        return {
            "url": self.url,
            "layers": dict(((name, authorized(perm)) for (name, perm) in
                            self.layers.iteritems()))
        }

    def check_permissions(self):
        # Check layers
        layers = self.get_requested_layers()
        for layer in layers:
            if self.layers.has_key(layer):
                perm = self.layers[layer]
            elif self.layers.has_key("DEFAULT"):
                perm = self.layers["DEFAULT"]
            else:
                continue
            if not authorized(perm):
                return False, "Not allowed to access layer: %s" % cgi.escape(layer)

        # TODO add other checks here (bbox, ...)

        return True, "Access allowed"

    def get_requested_layers(self):
        raise NotImplementedError()

    def get_requested_bbox(self):
        raise NotImplementedError()

class WMSLayer(Layer):
    def get_param(self, name):
        """Returns the request parameter given in argument, ignoring case.
           If not found, None is returned.
        """
        for k in request.params.keys():
            if k.lower() == name:
                return request.params[k]
        return None

    def get_requested_layers(self):
        layers = self.get_param("layers")
        if not layers:
            return []
        return layers.split(",")

class TileCacheLayer(Layer):
    def get_requested_layers(self):
        raise NotImplementedError("TODO TileCacheLayer::get_requested_layers")


class AuthProxyController(WSGIController):
    def __init__(self):
        self.layers = []
        self.alias_to_layer = {}

    def set_layers(self, layers):
        self.alias_to_layers = dict(((layer.alias, layer) for layer in layers))
        self.layers = layers

    @jsonify
    def get_permissions(self):
        return {
            "layer": [l.get_permissions() for l in self.layers]
        }

    def get(self, more):
        """Proxy action
        """
        # extract the first segment of the url
        m = re.match("/?([^/]+)(/?.*)$", more)
        if not m:
            response.status_code = 500
            return "Invalid URL, missing alias in the path"
        alias, more = m.groups()
        
        if not self.alias_to_layers.has_key(alias):
            response.status_code = 500
            return "Wrong alias %s" % cgi.escape(alias)
        layer = self.alias_to_layers[alias]

        allowed, msg = layer.check_permissions()
        if not allowed:
            # We don't use 403 to avoid triggering AuthKit login dialog
            response.status_code = 406
            return msg

        url = layer.url + more
        return self._proxy(url)

    def _proxy(self, url):
        """Do the actual action of proxying the call.
        """
        query = urlencode(request.params)
        full_url = url
        if query:
            if not full_url.endswith("?"):
                full_url += "?"
            full_url += query

        # build the request with its headers
        req = urllib2.Request(url=full_url)
        for header in request.headers:
            if header.lower() == "host":
                req.add_header(header, urlparse.urlparse(url)[1])
            else:
                req.add_header(header, request.headers[header])
        res = urllib2.urlopen(req)

        # add response headers
        i = res.info()
        response.status_code = res.code
        got_content_length = False
        for header in i:
            # We don't support serving the result as chunked
            if header.lower() == "transfer-encoding":
                continue
            if header.lower() == "content-length":
                got_content_length = True
            response.headers[header] = i[header]

        # return the result
        result = res.read()
        res.close()

        if not got_content_length:
            response.headers['content-length'] = str(len(result))
        return result


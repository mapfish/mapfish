import logging

from pylons.controllers import WSGIController
from pylons.decorators import jsonify
from pylons import config
from authkit.authorize.pylons_adaptors import authorize, authorized
from authkit.permissions import ValidAuthKitUser
from authkit.authorize import NotAuthorizedError
import simplejson

import sys
import os
import os.path
import inspect


log = logging.getLogger(__name__)

class SecurityController(WSGIController):
    def _get_master_permissions(self):
        """Read the permissions in the config/permissions.json file and return
           an object
        """
        perm_json = os.path.join(config.here, config['pylons.package'],
                                 "config", "permissions.json")

        permissions = {}
        modulename = "%s.config.permissions" % config['pylons.package']
        try:
            mod = __import__(modulename)
            for comp in modulename.split(".")[1:]:
                mod = getattr(mod, comp)
            permissions = mod.permissions
        except ImportError:
            log.debug("Couldn't find permission configuration module %s" % modulename)

        # compute permissions
        # TODO: calling authorized should be propagated inside nested dicts.
        permissions = dict(((key, authorized(perm)) for (key, perm) in
                            permissions.iteritems()))

        return permissions

    @jsonify
    def permissions(self):
        controllers_module_name = config['pylons.package'] + '.controllers'
        __import__(controllers_module_name)
        module = sys.modules[controllers_module_name]

        permissions = self._get_master_permissions()
        module_names = []

        # Iterate through all the controllers to call the method "get_permissions"
        # at the module level if available.
        # The value returned is merged into the permission object.

        if hasattr(module, '__path__'):
            for file in os.listdir(module.__path__[0]):
                if not file.endswith(".py"):
                    continue
                path = os.path.join(module.__path__[0], file)
                module_name = inspect.getmodulename(file)
                if not module_name or module_name == '__init__':
                    continue

                method_name = "get_permissions"
                full_module_name = controllers_module_name + '.' + module_name
                try:
                    __import__(full_module_name)
                except Exception, e:
                    log.warn("Failure while fetching controller in module %s (%s: %s)",
                             full_module_name, e.__class__, e)
                    continue
                mod = sys.modules[full_module_name]
                if not hasattr(mod, method_name):
                    continue
                get_permissions_method = getattr(mod, method_name)

                perms = get_permissions_method()
                if not isinstance(perms, dict):
                    raise Exception("Invalid permission type, should be dict, was %s" % type(perms))

                # TODO: should use a recursive udpate
                permissions.update(perms)

        return {"permissions": permissions}

class Deny:
    """A special AuthKit permission that always denies access
    """
    def check(self, app, environ, start_response):
        raise NotAuthorizedError("Not authorized at all")

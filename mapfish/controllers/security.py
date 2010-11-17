# 
# Copyright (c) 2008-2011 Camptocamp.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Camptocamp nor the names of its contributors may 
#    be used to endorse or promote products derived from this software 
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import logging

from pylons.controllers import WSGIController
from pylons.decorators import jsonify
from pylons import config
from authkit.authorize.pylons_adaptors import authorize, authorized
from authkit.permissions import ValidAuthKitUser
from authkit.authorize import NotAuthorizedError

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

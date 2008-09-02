from testapp.tests import *

import simplejson

class TestSecurityController(TestController):
    def _get_permissions(self, user):
        extra_environ = {}
        if user:
            extra_environ['REMOTE_USER'] = user
        response = self.app.get(url_for(controller='security',
                                        action='permissions'),
                                extra_environ=extra_environ)
        return simplejson.loads(response.body)['permissions']

    def test_permissions(self):
        permissions = self._get_permissions(None)

        assert permissions["application"] == False
        assert permissions["application.widgets.edit"] == False
        assert permissions.has_key("layer")
        # TODO test inside the layer properties

        permissions = self._get_permissions("alice")

        assert permissions["application"] == True
        assert permissions["application.widgets.edit"] == True
        assert permissions.has_key("layer")
        # TODO test inside the layer properties

        permissions = self._get_permissions("carol")

        assert permissions["application"] == True
        assert permissions["application.widgets.edit"] == False
        assert permissions.has_key("layer")
        # TODO test inside the layer properties

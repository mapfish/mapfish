from unittest import TestCase

import pylons
from pylons.util import ContextObj, PylonsContext

class TestWSGIController(TestCase):
    def setUp(self):
        c = ContextObj()
        py_obj = PylonsContext()
        py_obj.tmpl_context = c
        py_obj.request = py_obj.response = None
        self.environ = {'pylons.routes_dict': dict(action='index'),
                        'paste.config': dict(global_conf=dict(debug=True)),
                        'pylons.pylons': py_obj}
        pylons.tmpl_context._push_object(c)

    def tearDown(self):
        pylons.tmpl_context._pop_object()

    def get_response(self, **kargs):
        test_args = kargs.pop('test_args', {})
        url = kargs.pop('_url', '/')
        self.environ['pylons.routes_dict'].update(kargs)
        return self.app.get(url, extra_environ=self.environ, **test_args)

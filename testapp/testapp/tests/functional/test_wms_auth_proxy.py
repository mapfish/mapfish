from testapp.tests import *

import paste.fixture
import BaseHTTPServer
import threading
import urllib2
import time

# When running the tests, no HTTP server is started. To simulate a WMS server,
# a small HTTP server is run on port 9999.


class WMSHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Dummy response\n")

def run_httpd(server_class=BaseHTTPServer.HTTPServer,
              handler_class=WMSHTTPRequestHandler):
    server_address = ('', 9999)
    httpd = server_class(server_address, handler_class)
    server_running = True
    threading.Thread(target=httpd.serve_forever).start()
    # Wait some times to allow the server to startup
    import time
    time.sleep(0.5)

# Having the setup/teardown method inside TestWmsAuthProxyController is not working
# so let's have them at the module level.
def setup():
    run_httpd()

class TestWmsAuthProxyController(TestController):
    def check_access(self, alias, user, layers, expected_allowed):
        # url_for() is not working for "<url>/*more syntax. So hardcoding is
        # needed
        url = "/wms_auth_proxy/%s/wms?layers=%s" % (alias, ",".join(layers))
        allowed = True
        content = ""
        try:
            extra_environ = {}
            if user:
                extra_environ['REMOTE_USER'] = user
            content = self.app.get(url, extra_environ=extra_environ)
        except paste.fixture.AppError, e:
            print "Exception: %s %s" % (e.__class__, e)
            allowed = False
        assert expected_allowed == allowed, "Unexpected access to resource " + \
               "alias: %s user: %s layers: %s allowed: %s" % \
               (alias, user, layers, expected_allowed)
        # FIXME: can't make a distinction between invalid alias and denied response
        if expected_allowed:
            assert content, "Content shouldn't be empty (%s)" % repr(content)

    def test_basic(self):
        # Check that we fail for invalid alias
        try:
            self.check_access("non_existant", None, [], True)
        except AssertionError:
            pass
        else: 
            raise AssertionError("Should have raised an assertion about wrong alias")

    def test_no_restriction(self):
        self.check_access("no_restrictions", None, [], True)
        self.check_access("no_restrictions", "alice", ["parkings"], True)

    def test_default_deny(self):
        # Should we still allow access if no layers are given?
        self.check_access("default_deny", None, [], True)
        self.check_access("default_deny", "bob", [], True)
        self.check_access("default_deny", None, ["parkings"], False)
        self.check_access("default_deny", None, ["summits"], False)
        self.check_access("default_deny", None, ["parkings", "summits"], False)

        self.check_access("default_deny", "alice", ["parkings"], True)
        self.check_access("default_deny", "alice", ["parkings", "summits"], False)

    def test_default_allow(self):
        self.check_access("default_allow", None, [], True)
        self.check_access("default_allow", "bob", [], True)
        self.check_access("default_allow", None, ["parkings"], False)
        self.check_access("default_allow", None, ["summits"], True)
        self.check_access("default_allow", None, ["parkings", "summits"], False)

        self.check_access("default_allow", "alice", ["parkings"], True)
        self.check_access("default_allow", "alice", ["parkings", "summits"], True)

    def test_wms0(self):
        self.check_access("wms0", None, [], True)
        self.check_access("wms0", None, ["background"], True)
        self.check_access("wms0", None, ["parkings"], False)
        self.check_access("wms0", None, ["summits"], False)
        self.check_access("wms0", None, ["background", "parkings"], False)
        self.check_access("wms0", None, ["parkings", "summits"], False)
        self.check_access("wms0", None, ["background", "parkings", "summits"], False)

        self.check_access("wms0", "alice", [], True)
        self.check_access("wms0", "alice", ["background"], True)
        self.check_access("wms0", "alice", ["parkings"], True)
        self.check_access("wms0", "alice", ["summits"], False)
        self.check_access("wms0", "alice", ["background", "parkings"], True)
        self.check_access("wms0", "alice", ["parkings", "summits"], False)
        self.check_access("wms0", "alice", ["background", "parkings", "summits"], False)

        self.check_access("wms0", "bob", [], True)
        self.check_access("wms0", "bob", ["background"], True)
        self.check_access("wms0", "bob", ["parkings"], True)
        self.check_access("wms0", "bob", ["summits"], True)
        self.check_access("wms0", "bob", ["background", "parkings"], True)
        self.check_access("wms0", "bob", ["parkings", "summits"], True)
        self.check_access("wms0", "bob", ["background", "parkings", "summits"], True)

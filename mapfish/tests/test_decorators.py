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

import warnings
import unittest

from nose.tools import eq_, ok_

from paste.fixture import TestApp
from paste.registry import RegistryManager

from pylons.controllers import WSGIController
from pylons.testutil import ControllerWrap, SetupCacheGlobal

from shapely.geometry import Point
from geojson import Feature, FeatureCollection

from mapfish.decorators import MapFishEncoder, _jsonify, geojsonify
from mapfish.tests import TestWSGIController

class Controller(WSGIController):

    @geojsonify
    def return_feature(self):
        return Feature(id=1,
                       geometry=Point(1, 2),
                       properties={"strkey": "strval", "boolkey": True}
                       )

    @geojsonify
    def return_feature_collection(self):
        features = [
            Feature(id=1, geometry=Point(1, 2)),
            Feature(id=2, geometry=Point(3, 4))
            ]
        return FeatureCollection(features)

    @_jsonify(cls=MapFishEncoder, cb='foo')
    def return_feature_with_callback(self):
        return Feature(id=1,
                       geometry=Point(1, 2),
                       properties={"strkey": "strval", "boolkey": True}
                       )

environ = {}
app = ControllerWrap(Controller)
app = sap = SetupCacheGlobal(app, environ)
app = RegistryManager(app)
app = TestApp(app)

class Test(TestWSGIController):

    def setUp(self):
        self.app = app
        TestWSGIController.setUp(self)
        warnings.simplefilter('error', Warning)

    def tearDown(self):
        warnings.simplefilter('always', Warning)

    def test_feature(self):
        response = self.get_response(action='return_feature')
        assert response.status == 200
        assert response.response.content_type == 'application/json'
        assert response.body == '{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {"boolkey": true, "strkey": "strval"}, "id": 1}'

    def test_feature_collection(self):
        response = self.get_response(action='return_feature_collection')
        assert response.status == 200
        assert response.response.content_type == 'application/json'
        assert response.body == '{"type": "FeatureCollection", "features": [{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {}, "id": 1}, {"geometry": {"type": "Point", "coordinates": [3.0, 4.0]}, "type": "Feature", "properties": {}, "id": 2}]}'

    def test_feature_with_callback(self):
        response = self.get_response(action='return_feature_with_callback',
                                     test_args=dict(params={'foo': 'jsfunc'}))
        assert response.status == 200
        assert response.response.content_type == 'text/javascript'
        assert response.body == 'jsfunc({"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {"boolkey": true, "strkey": "strval"}, "id": 1});'

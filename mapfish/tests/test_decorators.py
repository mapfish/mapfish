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
                       properties={"key": "val"}
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
                       properties={"key": "val"}
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
        assert response.body == '{"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {"key": "val"}, "id": 1}'

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
        assert response.body == 'jsfunc({"geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "type": "Feature", "properties": {"key": "val"}, "id": 1});'

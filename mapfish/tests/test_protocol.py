""" This module includes unit tests for protocol.py """

from StringIO import StringIO

import unittest

from sqlalchemy import MetaData, Column, create_engine
from sqlalchemy import types
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from geojson import dumps, Feature

from shapely.geometry.polygon import Polygon

from geoalchemy import GeometryColumn, Geometry

from mapfish.sqlalchemygeom import GeometryTableMixIn
from mapfish.lib.filters import logical, comparison, spatial

#
# Setup
# 

Base = declarative_base(metadata=MetaData())

class MappedClass(Base, GeometryTableMixIn):
    __tablename__ = "table"
    id = Column(types.Integer, primary_key=True)
    text = Column(types.Unicode)
    geom = GeometryColumn(Geometry(dimension=2, srid=4326))

class FakeRequest(object):
    def __init__(self, params=None):
        self.params = params
        self.environ = {}

    def _setbody(self, body):
        self.environ["wsgi.input"] = StringIO(body)
        self.environ["CONTENT_LENGTH"] = len(body)
    body = property(None, _setbody)

class FakeResponse(object):
    def __init__(self):
        self.status = 0

# create a session in the same way it's done in a typical Pylons app
engine = create_engine('postgresql://user:user@no_connection/no_db', echo=True)
sm = orm.sessionmaker(autoflush=True, autocommit=False, bind=engine)
Session = orm.scoped_session(sm)

def query_to_str(query):
    """Helper method which compiles a query using a database engine
    """
    return unicode(query.statement.compile(engine)).encode('ascii', 'backslashreplace')
#
# Test
# 

class Test(unittest.TestCase):

    def test_create_geom_filter(self):
        from mapfish.lib.protocol import create_geom_filter
        request = FakeRequest(
            {"box": "-45,-5,40,0", "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        assert isinstance(filter, spatial.Spatial)
        assert filter.type == spatial.Spatial.BOX
        assert filter.values["tolerance"] == 1
        assert filter.values["epsg"] == 900913
    
        request = FakeRequest(
            {"bbox": "-45,-5,40,0", "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        assert isinstance(filter, spatial.Spatial)
        assert filter.type == spatial.Spatial.BOX
        assert filter.values["tolerance"] == 1
        assert filter.values["epsg"] == 900913
    
        request = FakeRequest(
            {"lon": "-45", "lat": "5", "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        assert isinstance(filter, spatial.Spatial)
        assert filter.type == spatial.Spatial.WITHIN
        assert filter.values["tolerance"] == 1
        assert filter.values["epsg"] == 900913
    
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = FakeRequest(
            {"geometry": dumps(poly), "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        assert isinstance(filter, spatial.Spatial)
        assert filter.type == spatial.Spatial.GEOMETRY
        assert filter.values["tolerance"] == 1
        assert filter.values["epsg"] == 900913
    
        request = FakeRequest({})
        filter = create_geom_filter(request, MappedClass)
        assert filter is None
        
        request = FakeRequest({"lon": "-45", "lat": "5"})
        filter = create_geom_filter(request, MappedClass, additional_params='unit=KM')
        assert filter.additional_params is not None
    
    
    def test_create_attr_filter(self):
        from mapfish.lib.protocol import create_attr_filter
        request = FakeRequest(
            {"queryable": "id", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.EQUAL_TO
        assert filter.values["value"] == "1"
    
        request = FakeRequest(
            {"queryable": "id", "id__lt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.LOWER_THAN
        assert filter.values["value"] == "1"
    
        request = FakeRequest(
            {"queryable": "id", "id__lte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.LOWER_THAN_OR_EQUAL_TO
        assert filter.values["value"] == "1"
    
        request = FakeRequest(
            {"queryable": "id", "id__gt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.GREATER_THAN
        assert filter.values["value"] == "1"
    
        request = FakeRequest(
            {"queryable": "id", "id__gte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.GREATER_THAN_OR_EQUAL_TO
        assert filter.values["value"] == "1"
    
        request = FakeRequest(
            {"queryable": "text", "text__like": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.LIKE
        assert filter.values["value"] == "foo"
    
        request = FakeRequest(
            {"queryable": "text", "text__ilike": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, comparison.Comparison)
        assert filter.type == comparison.Comparison.ILIKE
        assert filter.values["value"] == "foo"
    
        request = FakeRequest(
            {"queryable": "text,id", "text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, logical.Logical)
        assert filter.type == logical.Logical.AND
        assert len(filter.filters) == 2
    
        request = FakeRequest(
            {"text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert filter is None
    
    
    def test_asbool(self):
        from mapfish.lib.protocol import asbool
        assert asbool(0) == False
        assert asbool(1) == True
        assert asbool(2) == True
        assert asbool("0") == False
        assert asbool("1") == True
        assert asbool("false") == False
        assert asbool("true") == True
        assert asbool("False") == False
        assert asbool("True") == True
        assert asbool(u"0") == False
        assert asbool(u"1") == True
        assert asbool(u"false") == False
        assert asbool(u"true") == True
        assert asbool(u"False") == False
        assert asbool(u"True") == True
    
    def test_protocol_query(self):
        from mapfish.lib.protocol import Protocol, create_attr_filter
        proto = Protocol(Session, MappedClass)
    
        request = FakeRequest({})
        query = proto._query(request, execute=False)
        stmt = query.statement
        stmtm_str = stmt.compile(engine)
        assert "SELECT" in query_to_str(query)
    
        request = FakeRequest({"queryable": "id", "id__eq": "1"})
        query = proto._query(request, execute=False)
        assert "WHERE" in query_to_str(query)
    
        request = FakeRequest({"queryable": "id", "id__eq": "1"})
        filter = create_attr_filter(request, MappedClass)
        query = proto._query(FakeRequest({}), filter=filter, execute=False)
        assert "WHERE" in query_to_str(query)
    
        request = FakeRequest({"limit": "2"})
        query = proto._query(request, execute=False)
        assert "LIMIT 2" in query_to_str(query)
    
        request = FakeRequest({"maxfeatures": "2"})
        query = proto._query(request, execute=False)
        assert "LIMIT 2" in query_to_str(query)
    
        request = FakeRequest({"limit": "2", "offset": "10"})
        query = proto._query(request, execute=False)
        assert "OFFSET 10" in query_to_str(query)
    
        request = FakeRequest({"order_by": "text"})
        query = proto._query(request, execute=False)
        assert "ORDER BY" in query_to_str(query)
        assert "ASC" in query_to_str(query)
    
        request = FakeRequest({"sort": "text"})
        query = proto._query(request, execute=False)
        assert "ORDER BY" in query_to_str(query)
        assert "ASC" in query_to_str(query)
    
        request = FakeRequest({"order_by": "text", "dir": "DESC"})
        query = proto._query(request, execute=False)
        assert "ORDER BY" in query_to_str(query)
        assert "DESC" in query_to_str(query)
    
    def test_protocol_create(self):
        from mapfish.lib.protocol import Protocol
        proto = Protocol(Session, MappedClass)
        request = FakeRequest({})
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        response = FakeResponse()
        proto.create(request, response, execute=False)
        assert response.status ==  201
        assert len(Session.new) == 2
        for obj in Session.new:
            assert obj["text"] == "foo"
            assert obj.geometry.shape.x == 45
            assert obj.geometry.shape.y == 5
        Session.rollback()

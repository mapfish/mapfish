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

""" This module includes unit tests for protocol.py """

from StringIO import StringIO

import unittest

from nose.tools import eq_, ok_

from sqlalchemy import MetaData, Column, create_engine
from sqlalchemy import types, orm, sql
from sqlalchemy.ext.declarative import declarative_base

from geojson import dumps, Feature

from shapely import wkt, wkb
from shapely.geometry.polygon import Polygon

from geoalchemy import GeometryColumn, Geometry

from mapfish.sqlalchemygeom import GeometryTableMixIn

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

def _compiled_to_string(compiled_filter):
    """Helper method which converts a compiled SQL expression
    into a string.
    """
    return unicode(compiled_filter).encode('ascii', 'backslashreplace')

#
# Test
# 

class Test(unittest.TestCase):

    def test_box_filter(self):
        from mapfish.protocol import create_geom_filter
        request = FakeRequest(
            {"bbox": "-180,-90,180,90", "tolerance": "1"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1
   
        request = FakeRequest(
            {"bbox": "-180,-90,180,90", "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1

    def test_within_filter(self):
        from mapfish.protocol import create_geom_filter
        request = FakeRequest(
            {"lon": "40", "lat": "5", "tolerance": "1"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)'))
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1

        request = FakeRequest(
            {"lon": "40", "lat": "5", "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)'))
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1

    def test_polygon_filter(self):
        from mapfish.protocol import create_geom_filter
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = FakeRequest(
            {"geometry": dumps(poly), "tolerance": "1"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(poly)
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1

        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
        request = FakeRequest(
            {"geometry": dumps(poly), "tolerance": "1", "epsg": "900913"}
        )
        filter = create_geom_filter(request, MappedClass)
        compiled_filter = filter.compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(poly)
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1        #assert isinstance(filter, sql.expression.ClauseElement)

    def test_geom_filter_misc(self):
        from mapfish.protocol import create_geom_filter
        request = FakeRequest({})
        filter = create_geom_filter(request, MappedClass)
        assert filter is None

    def test_create_attr_filter(self):
        from mapfish.protocol import create_attr_filter
        request = FakeRequest(
            {"queryable": "id", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id == "1").compare(filter)

        request = FakeRequest(
            {"queryable": "id", "id__lt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id < "1").compare(filter)

        request = FakeRequest(
            {"queryable": "id", "id__lte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id <= "1").compare(filter)

        request = FakeRequest(
            {"queryable": "id", "id__gt": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id > "1").compare(filter)

        request = FakeRequest(
            {"queryable": "id", "id__gte": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.id >= "1").compare(filter)

        request = FakeRequest(
            {"queryable": "text", "text__like": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.text.like("foo")).compare(filter)

        request = FakeRequest(
            {"queryable": "text", "text__ilike": "foo"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert isinstance(filter, sql.expression.ClauseElement)
        assert sql.and_(MappedClass.text.ilike("foo")).compare(filter)

        request = FakeRequest(
            {"queryable": "text,id", "text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert (sql.and_(MappedClass.text.ilike("foo"), MappedClass.id == "1")).compare(filter)

        request = FakeRequest(
            {"text__ilike": "foo", "id__eq": "1"}
        )
        filter = create_attr_filter(request, MappedClass)
        assert filter is None
    
    
    def test_asbool(self):
        from mapfish.protocol import asbool
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
        from mapfish.protocol import Protocol, create_attr_filter
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
        from mapfish.protocol import Protocol
        proto = Protocol(Session, MappedClass)
        request = FakeRequest({})
        request.body = '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}, {"type": "Feature", "properties": {"text": "foo"}, "geometry": {"type": "Point", "coordinates": [45, 5]}}]}'
        response = FakeResponse()
        proto.create(request, response, execute=False)
        assert response.status ==  201
        assert len(Session.new) == 2
        for obj in Session.new:
            assert obj["text"] == "foo"
            assert obj._mf_shape.x == 45
            assert obj._mf_shape.y == 5
        Session.rollback()

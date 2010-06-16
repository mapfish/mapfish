""" Tests in this module test that the SQL expressions returned by the MapFish
    filters are correct. These tests are SQLAlchemy integration tests. """

import unittest
from nose import with_setup
from nose.tools import eq_, ok_

from sqlalchemy import MetaData, Table, Column, create_engine
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.orm import mapper
from sqlalchemy.sql import func, and_
from sqlalchemy.ext.declarative import declarative_base

from shapely import wkt, wkb
from shapely.geometry.polygon import Polygon

from geojson import dumps

from geoalchemy import GeometryColumn, Geometry

from mapfish.sqlalchemygeom import GeometryTableMixIn
from mapfish.lib.filters import spatial, comparison, featureid, logical

#
# Setup
#

# create a dummy engine, no connection is established, we only need the database dialect  
engine = create_engine('postgresql://user:user@no_connection/no_db', echo=True)
Base = declarative_base(metadata=MetaData())

class MappedClass(Base, GeometryTableMixIn):
    __tablename__ = "table"
    id = Column(Integer, primary_key=True)
    text = Column(Unicode)
    geom = GeometryColumn(Geometry(dimension=2, srid=4326))


def _compiled_to_string(compiled_filter):
    """Helper method which converts a compiled SQL expression
    into a string.
    """
    return unicode(compiled_filter).encode('ascii', 'backslashreplace')


class Test(unittest.TestCase):
    
    #
    # Test Spatial
    # 

    def test_spatial_box(self):
        # with epsg undefined
        filter = spatial.Spatial(
            spatial.Spatial.BOX,
            MappedClass.geometry_column(),
            box=[-180, -90, 180, 90],
            tolerance=1
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1
    
        # with epsg defined
        filter = spatial.Spatial(
            spatial.Spatial.BOX,
            MappedClass.geometry_column(),
            box=[-180, -90, 180, 90],
            tolerance=1,
            epsg=900913
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1
    
    def test_spatial_within(self):
        # with epsg undefined
        filter = spatial.Spatial(
            spatial.Spatial.WITHIN,
            MappedClass.geometry_column(),
            lon=40, lat=5, tolerance=1
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)'))
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1
     
        # with epsg defined
        filter = spatial.Spatial(
            spatial.Spatial.WITHIN,
            MappedClass.geometry_column(),
            lon=40, lat=5, tolerance=1, epsg=900913 
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(wkt.loads('POINT (40 5)'))
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1
    
    def test_spatial_geometry(self):
        poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))
    
        # with epsg undefined
        filter = spatial.Spatial(
            spatial.Spatial.GEOMETRY,
            MappedClass.geometry_column(),
            geometry=dumps(poly),
            tolerance=1
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && "table".geom) AND (ST_Expand("table".geom, %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance("table".geom, GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(poly)
        assert params["GeomFromWKB_2"] == 4326
        assert params["ST_Expand_1"] == 1
        assert params["ST_Distance_1"] == 1
    
        # with epsg defined
        filter = spatial.Spatial(
            spatial.Spatial.GEOMETRY,
            MappedClass.geometry_column(),
            geometry=dumps(poly),
            tolerance=1,
            epsg=900913
        )
        compiled_filter = filter.to_sql_expr().compile(engine)
        params = compiled_filter.params
        filter_str = _compiled_to_string(compiled_filter)
        eq_(filter_str, '(ST_Expand(GeomFromWKB(%(GeomFromWKB_1)s, %(GeomFromWKB_2)s), %(ST_Expand_1)s) && ST_Transform("table".geom, %(param_1)s)) AND (ST_Expand(ST_Transform("table".geom, %(param_2)s), %(ST_Expand_2)s) && GeomFromWKB(%(GeomFromWKB_3)s, %(GeomFromWKB_4)s)) AND ST_Distance(ST_Transform("table".geom, %(param_3)s), GeomFromWKB(%(GeomFromWKB_5)s, %(GeomFromWKB_6)s)) <= %(ST_Distance_1)s')
        assert wkb.loads(str(params["GeomFromWKB_1"])).equals(poly)
        assert params["GeomFromWKB_2"] == 900913
        assert params["ST_Expand_1"] == 1
        assert params["param_1"] == 900913
        assert params["ST_Distance_1"] == 1
    
    #
    # Test Comparison
    #
    
    def test_comparison_equalto(self):
        filter = comparison.Comparison(
            comparison.Comparison.EQUAL_TO,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id = :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_notequalto(self):
        filter = comparison.Comparison(
            comparison.Comparison.NOT_EQUAL_TO,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id != :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_lowerthan(self):
        filter = comparison.Comparison(
            comparison.Comparison.LOWER_THAN,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id < :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_lowerthanorequalto(self):
        filter = comparison.Comparison(
            comparison.Comparison.LOWER_THAN_OR_EQUAL_TO,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id <= :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_greaterthan(self):
        filter = comparison.Comparison(
            comparison.Comparison.GREATER_THAN,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id > :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_greaterthanorequalto(self):
        filter = comparison.Comparison(
            comparison.Comparison.GREATER_THAN_OR_EQUAL_TO,
            MappedClass.id,
            value=1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id >= :id_1'
        assert params["id_1"] == 1
    
    def test_comparison_between(self):
        filter = comparison.Comparison(
            comparison.Comparison.BETWEEN,
            MappedClass.id,
            lower_bound=1, upper_bound=2
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id <= :id_1 AND "table".id >= :id_2'
        assert params["id_1"] == 2
        assert params["id_2"] == 1
    
    def test_comparison_like(self):
        filter = comparison.Comparison(
            comparison.Comparison.LIKE,
            MappedClass.text,
            value="foo"
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".text LIKE :text_1'
        assert params["text_1"] == "foo"
    
    def test_comparison_ilike(self):
        filter = comparison.Comparison(
            comparison.Comparison.ILIKE,
            MappedClass.text,
            value="foo"
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == 'lower("table".text) LIKE lower(:text_1)'
        assert params["text_1"] == "foo"
    
    #
    # Test FeatureId
    #
    
    def test_featureid(self):
        filter = featureid.FeatureId(
            MappedClass.id,
            1
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id = :id_1'
        assert params["id_1"] == 1
    
    #
    # Test Logical
    #
         
    def test_logical_not(self):
        filter = logical.Logical(
            logical.Logical.NOT,
            filters=[
                comparison.Comparison(
                    comparison.Comparison.EQUAL_TO,
                    MappedClass.id,
                    value=1
                )
            ]
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id != :id_1'
        assert params["id_1"] == 1
    
        filter =  logical.Logical(
            logical.Logical.NOT,
            filters=[
                comparison.Comparison(
                    comparison.Comparison.LIKE,
                    MappedClass.text,
                    value="foo"
                )
            ]
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".text NOT LIKE :text_1'
        assert params["text_1"] == "foo"
    
    def test_logical_and(self):
        filter = logical.Logical(
            logical.Logical.AND,
            filters=[
                comparison.Comparison(
                    comparison.Comparison.EQUAL_TO,
                    MappedClass.id,
                    value=1
                ),
                comparison.Comparison(
                    comparison.Comparison.LIKE,
                    MappedClass.text,
                    value="foo"
                )
            ]
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id = :id_1 AND "table".text LIKE :text_1'
        assert params["id_1"] == 1
        assert params["text_1"] == "foo"
    
    def test_logical_or(self):
        filter = logical.Logical(
            logical.Logical.OR,
            filters=[
                comparison.Comparison(
                    comparison.Comparison.EQUAL_TO,
                    MappedClass.id,
                    value=1
                ),
                comparison.Comparison(
                    comparison.Comparison.LIKE,
                    MappedClass.text,
                    value="foo"
                )
            ]
        )
        filter = filter.to_sql_expr()
        params = filter.compile().params
        assert str(filter) == '"table".id = :id_1 OR "table".text LIKE :text_1'
        assert params["id_1"] == 1
        assert params["text_1"] == "foo"

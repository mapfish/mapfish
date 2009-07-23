""" Tests in this module test that the SQL expressions returned by the MapFish
    filters are correct. These tests are SQLAlchemy integration tests. """

from nose import with_setup

from sqlalchemy import MetaData, Table, Column
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.orm import mapper
from sqlalchemy.sql import func, and_

from shapely import wkt
from shapely.geometry.polygon import Polygon

from geojson import dumps

from mapfish.sqlalchemygeom import Geometry, GeometryTableMixIn
from mapfish.lib.filters import spatial, comparison, featureid, logical

#
# Setup
# 

table = Table("table", MetaData(),
    Column("id", Integer, primary_key=True),
    Column("text", Unicode),
    Column("geom", Geometry(4326))
)

class MappedClass(GeometryTableMixIn):
    __table__ = table

mapper(MappedClass, table)

#
# Test Spatial
# 

def test_spatial_box():
    # with epsg undefined
    filter = spatial.Spatial(
        spatial.Spatial.BOX,
        MappedClass.geometry_column(),
        box=[-180, -90, 180, 90],
        tolerance=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && "table".geom) AND distance("table".geom, geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
    assert params["geomfromtext_2"] == 4326
    assert params["expand_1"] == 1
    assert params["distance_1"] == 1

    # with epsg defined
    filter = spatial.Spatial(
        spatial.Spatial.BOX,
        MappedClass.geometry_column(),
        box=[-180, -90, 180, 90],
        tolerance=1,
        epsg=900913
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && transform("table".geom, :transform_1)) AND distance(transform("table".geom, :transform_1), geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(wkt.loads('POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'))
    assert params["geomfromtext_2"] == 900913
    assert params["expand_1"] == 1
    assert params["transform_1"] == 900913
    assert params["distance_1"] == 1

def test_spatial_within():
    # with epsg undefined
    filter = spatial.Spatial(
        spatial.Spatial.WITHIN,
        MappedClass.geometry_column(),
        lon=40, lat=5, tolerance=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && "table".geom) AND distance("table".geom, geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(wkt.loads('POINT (40 5)'))
    assert params["geomfromtext_2"] == 4326
    assert params["expand_1"] == 1
    assert params["distance_1"] == 1
 
    # with epsg defined
    filter = spatial.Spatial(
        spatial.Spatial.WITHIN,
        MappedClass.geometry_column(),
        lon=40, lat=5, tolerance=1, epsg=900913 
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && transform("table".geom, :transform_1)) AND distance(transform("table".geom, :transform_1), geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(wkt.loads('POINT (40 5)'))
    assert params["geomfromtext_2"] == 900913
    assert params["expand_1"] == 1
    assert params["transform_1"] == 900913
    assert params["distance_1"] == 1

def test_spatial_geometry():
    poly = Polygon(((1, 2), (1, 3), (2, 3), (2, 2), (1, 2)))

    # with epsg undefined
    filter = spatial.Spatial(
        spatial.Spatial.GEOMETRY,
        MappedClass.geometry_column(),
        geometry=dumps(poly),
        tolerance=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && "table".geom) AND distance("table".geom, geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(poly)
    assert params["geomfromtext_2"] == 4326
    assert params["expand_1"] == 1
    assert params["distance_1"] == 1

    # with epsg defined
    filter = spatial.Spatial(
        spatial.Spatial.GEOMETRY,
        MappedClass.geometry_column(),
        geometry=dumps(poly),
        tolerance=1,
        epsg=900913
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '(expand(geomfromtext(:geomfromtext_1, :geomfromtext_2), :expand_1) && transform("table".geom, :transform_1)) AND distance(transform("table".geom, :transform_1), geomfromtext(:geomfromtext_1, :geomfromtext_2)) <= :distance_1'
    assert wkt.loads(params["geomfromtext_1"]).equals(poly)
    assert params["geomfromtext_2"] == 900913
    assert params["expand_1"] == 1
    assert params["transform_1"] == 900913
    assert params["distance_1"] == 1

#
# Test Comparison
#

def test_comparison_equalto():
    filter = comparison.Comparison(
        comparison.Comparison.EQUAL_TO,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id = :id_1'
    assert params["id_1"] == 1

def test_comparison_notequalto():
    filter = comparison.Comparison(
        comparison.Comparison.NOT_EQUAL_TO,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id != :id_1'
    assert params["id_1"] == 1

def test_comparison_lowerthan():
    filter = comparison.Comparison(
        comparison.Comparison.LOWER_THAN,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id < :id_1'
    assert params["id_1"] == 1

def test_comparison_lowerthanorequalto():
    filter = comparison.Comparison(
        comparison.Comparison.LOWER_THAN_OR_EQUAL_TO,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id <= :id_1'
    assert params["id_1"] == 1

def test_comparison_greaterthan():
    filter = comparison.Comparison(
        comparison.Comparison.GREATER_THAN,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id > :id_1'
    assert params["id_1"] == 1

def test_comparison_greaterthanorequalto():
    filter = comparison.Comparison(
        comparison.Comparison.GREATER_THAN_OR_EQUAL_TO,
        MappedClass.id,
        value=1
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".id >= :id_1'
    assert params["id_1"] == 1

def test_comparison_between():
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

def test_comparison_like():
    filter = comparison.Comparison(
        comparison.Comparison.LIKE,
        MappedClass.text,
        value="foo"
    )
    filter = filter.to_sql_expr()
    params = filter.compile().params
    assert str(filter) == '"table".text LIKE :text_1'
    assert params["text_1"] == "foo"

def test_comparison_ilike():
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

def test_featureid():
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
     
def test_logical_not():
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

def test_logical_and():
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

def test_logical_or():
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

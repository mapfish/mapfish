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

__all__ = ['GeometryTableMixIn']


"""
SQLAlchemy geometry type support
see: http://www.sqlalchemy.org/docs/04/types.html#types_custom

  Example
  -------
from sqlalchemy import *
from mapfish.sqlalchemygeom import GeometryTableMixIn
from geoalchemy import GeometryColumn, Geometry

# see: http://www.sqlalchemy.org/docs/dbengine.html
db = create_engine('postgres://www-data:www-data@kirishima.c2c:5433/epfl')

metadata = MetaData()
metadata.connect(db)

Base = declarative_base(metadata=metadata)

class Wifi(Base, GeometryTableMixIn):
    __tablename__ = 'wifi'
    gid = Column(types.Integer, primary_key=True)
    # add more columns here ...
    the_geom = GeometryColumn(Geometry(dimension=2, srid=4326))


# basic select
r = Wifi.__table__.select(Wifi.gid == 10).execute()
w = r.fetchone()
print w.the_geom

# advanced select
from shapely.geometry.point import Point
from geoalchemy import functions, WKBSpatialElement

me = Point(532778, 152205)

r = Wifi.__table__.select(functions.distance(Wifi.the_geom, WKBSpatialElement(buffer(me.wkb))) < 100).execute()
print [(i.gid, i.the_geom.distance(me)) for i in r]

## update
#u = Wifi.__table__.update(Wifi.the_geom == 10)
#w.the_geom.y += 9.0
#u.execute(the_geom = w.the_geom)
"""

from shapely.wkb import loads
from geojson import Feature

from geoalchemy import Geometry as GeometryBase
from geoalchemy.functions import BaseFunction, parse_clause
from geoalchemy.geometry import GeometryExtensionColumn
from geoalchemy.spatialite import SQLiteSpatialDialect

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import and_, text, table, column 
from sqlalchemy import select, func
from sqlalchemy.schema import Column

from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy.dialects.mysql.base import MySQLDialect
from sqlalchemy.dialects.oracle.base import OracleDialect

class GeometryTableMixIn(object):

    """Class to be mixed in mapped classes.
    
       When used the mapped class exposes

       ``geometry_column()``
           Class method returning the ``Column`` object corresponding to the
           geometry column.
       
       ``primary_key_column()``
           Class method returning the ``Column`` object corresponding to the
           primary key.

       When used the mapped object exposes

       ``geometry``
           The Shapely geometry object representing the geometry value in the
           database.
           
       ``fid``
           The value of the primary key.

       ``toFeature()``
           Method returning a ``geojson.Feature`` object that corresponds to
           this object.

       Example::
       
            Base = declarative_base(metadata=metadata)

            class Line(Base, GeometryTableMixIn):
                __tablename__ = 'lines'
                __table_args__ = {
                        'autoload' : True,
                        'autoload_with' : engine
                    }
                
                the_geom = GeometryColumn(Geometry(dimension=2, srid=4326))

    """

    exported_keys = None
    __column_cache__ = None

    def _getfid(self):
        return getattr(self, self.primary_key_column().name)

    def _setfid(self, val):
        setattr(self, self.primary_key_column().name, val)

    fid = property(_getfid, _setfid)
    """ The value of the primary key."""

    def _getgeom(self):
        return getattr(self, self.geometry_column().name)

    def _setgeom(self, val):
        setattr(self, self.geometry_column().name, val)

    geometry = property(_getgeom, _setgeom)
    """ The Shapely geometry object associated to the geometry value."""

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        if key in self.__table__.c.keys():
            setattr(self, key, val)

    def __contains__(self, key):
        return hasattr(self, key)

    @classmethod
    def geometry_column(cls):
        """ Returns the table's geometry column or None if the table has no geometry column. """
        if cls.__column_cache__ is None or "geometry" not in cls.__column_cache__:
            columns = [c for c in cls.__table__.columns if isinstance(c.type, GeometryBase)]
            if not columns:
                return None
            elif len(columns) > 1:
                raise Exception("There is more than one geometry column")
            else:
                column = columns.pop()
                cls.__column_cache__ = dict(geometry=column)
        return cls.__column_cache__["geometry"] 

    @classmethod
    def primary_key_column(cls):
        """ Returns the table's primary key column """
        if cls.__column_cache__ is None or "primary_key" not in cls.__column_cache__:
            keys = [k for k in cls.__table__.primary_key]
            if not keys:
                raise Exception("No primary key found !")
            elif len(keys) > 1:
                raise Exception("There is more than one primary key column")
            else:
                cls.__column_cache__ = dict(primary_key=keys.pop())
        return cls.__column_cache__["primary_key"]

    def toFeature(self):
        """Create and return a ``geojson.Feature`` object from this mapped object."""
        if not self.exported_keys:
            exported = self.__table__.c.keys()
        else:
            exported = self.exported_keys

        fid_column = self.primary_key_column().name
        geom_column = self.geometry_column().name

        attributes = {}
        for k in exported:
            k = str(k)
            if k != fid_column and k != geom_column and hasattr(self, k):
                attributes[k] = getattr(self, k)
        
        if hasattr(self.geometry, 'shape') and self.geometry.shape is not None:
            # we already have the geometry as Shapely geometry (when updating/inserting)
            geometry = self.geometry.shape
        elif hasattr(self.geometry, 'geom_wkb') and self.geometry.geom_wkb is not None:
            # create a Shapely geometry from the WKB geometry returned from the database
            geometry = loads(str(self.geometry.geom_wkb))
        else:
            geometry = None

        return Feature(id=self.fid, 
                       geometry=geometry,
                       properties=attributes,
                       bbox=None if geometry is None else geometry.bounds)


class within_distance(BaseFunction):
    """This class is used as SQLAlchemy function to query features that are 
    within a certain distance of a geometry. 
    When it is used inside a query, the SQLAlchemy compiler calls the 
    method __compile_within_distance.
    """
    pass

@compiles(within_distance)
def __compile_within_distance(element, compiler, **kw):
    if isinstance(compiler.dialect, PGDialect):
        function = __within_distance_pg
    elif isinstance(compiler.dialect, MySQLDialect):
        function = __within_distance_mysql
    elif isinstance(compiler.dialect, SQLiteDialect):
        function = __within_distance_spatialite
    elif isinstance(compiler.dialect, OracleDialect):
        function = __within_distance_oracle
    else:
        raise NotImplementedError("Operation 'within_distance' is not supported by '%s'" % (compiler.dialect))
    
    arguments = list(element.arguments)
    return compiler.process(function(compiler, parse_clause(arguments.pop(0), compiler), 
                                     parse_clause(arguments.pop(0), compiler), arguments.pop(0), *arguments))
    
def __within_distance_pg(compiler, geom1, geom2, distance):
    """Implementation of within_distance for PostGIS
    
    ST_DWithin in early versions of PostGIS 1.3 does not work when
    distance = 0. So we are directly using the (correct) internal definition.
    Note that the definition changed in version 1.3.4, see also:
    http://postgis.refractions.net/docs/ST_DWithin.html
    """
    return and_(func.ST_Expand(geom2, distance).op('&&')(geom1),
                    func.ST_Expand(geom1, distance).op('&&')(geom2),
                    func.ST_Distance(geom1, geom2) <= distance)

def __within_distance_mysql(compiler, geom1, geom2, distance):
    """Implementation of within_distance for MySQL
    
    MySQL does not support the function distance, so we are doing
    a kind of "mbr_within_distance".
    The MBR of 'geom2' is expanded with the amount of 'distance' by
    manually changing the coordinates. Then we test if 'geom1' intersects
    this expanded MBR.
    """
    mbr = func.ExteriorRing(func.Envelope(geom2))
    
    lower_left = func.StartPoint(mbr)
    upper_right = func.PointN(mbr, 3)
    
    xmin = func.X(lower_left)
    ymin = func.Y(lower_left)
    xmax = func.X(upper_right)
    ymax = func.Y(upper_right)
    
    return func.Intersects(
            geom1,
            func.GeomFromText(
                func.Concat('Polygon((',
                       xmin - distance, ' ', ymin - distance, ',',
                       xmax + distance, ' ', ymin - distance, ',',
                       xmax + distance, ' ', ymax + distance, ',',
                       xmin - distance, ' ', ymax + distance, ',',
                       xmin - distance, ' ', ymin - distance, '))'), func.srid(geom2)
                )                                              
            )

def __within_distance_spatialite(compiler, geom1, geom2, distance):
    """Implementation of within_distance for Spatialite
    """
    if isinstance(geom1, GeometryExtensionColumn) and geom1.type.spatial_index and SQLiteSpatialDialect.supports_rtree(compiler.dialect):
        """If querying on a geometry column that also has a spatial index,
        then make use of this index.
        
        see: http://www.gaia-gis.it/spatialite/spatialite-tutorial-2.3.1.html#t8 and
        http://groups.google.com/group/spatialite-users/browse_thread/thread/34609c7a711ac92d/7688ced3f909039c?lnk=gst&q=index#f6dbc235471574db
        """
        return and_(
                    func.Distance(geom1, geom2) <= distance,
                    table(geom1.table.fullname, column("rowid")).c.rowid.in_(
                        select([table("idx_%s_%s" % (geom1.table.fullname, geom1.key), column("pkid")).c.pkid]).where(
                            and_(text('xmin') >= func.MbrMinX(geom2) - distance,
                            and_(text('xmax') <= func.MbrMaxX(geom2) + distance,
                            and_(text('ymin') >= func.MbrMinY(geom2) - distance,
                                 text('ymax') <= func.MbrMaxY(geom2) + distance)))
                            )
                        )
                    )
        
    else:
        return func.Distance(geom1, geom2) <= distance
    


def __within_distance_oracle(compiler, geom1, geom2, distance, additional_params={}):
    """Implementation of within_distance for Oracle
    
    If the first parameter is a geometry column, then the Oracle operator SDO_WITHIN_DISTANCE
    is called and Oracle makes use of the spatial index of this column.
    
    If the first parameter is not a geometry column but a function, which is the case when a coordinate 
    transformation had to be added by the spatial filter, then the function SDO_GEOM.WITHIN_DISTANCE
    is called. SDO_GEOM.WITHIN_DISTANCE does not make use of a spatial index and requires
    additional parameters: either a tolerance value or a dimension information array (DIMINFO)
    for both geometries. These parameters can be specified when defining the spatial filter, e.g.::
    
        additional_params={'tol': '0.005'}
        
        or
        
        from sqlalchemy.sql.expression import text
        diminfo = text("MDSYS.SDO_DIM_ARRAY("\
            "MDSYS.SDO_DIM_ELEMENT('LONGITUDE', -180, 180, 0.000000005),"\
            "MDSYS.SDO_DIM_ELEMENT('LATITUDE', -90, 90, 0.000000005)"\
            ")")
        additional_params={'dim1': diminfo, 'dim2': diminfo}
        
        filter = create_default_filter(request, Spot, additional_params=additional_params)
        proto.count(request, filter=filter)
        
    For its distance calculation Oracle by default uses meter as unit for geodetic data (like EPSG:4326) 
    and otherwise the 'unit of measurement associated with the data'. The unit used for the 'distance' value
    can be changed by adding an entry to 'additional_params'. Valid units are defined in the 
    view 'sdo_dist_units'::
    
        additional_params={'params': 'unit=km'}
        
    SDO_WITHIN_DISTANCE accepts further parameters, which can also be set using the name 'params'
    together with the unit::
    
        additional_params={'params': 'unit=km max_resolution=10'}
        
    
    Valid options for 'additional_params' are:
    
        params
            A String containing additional parameters, for example the unit.
            
        tol
            The tolerance value used for the SDO_GEOM.WITHIN_DISTANCE function call.
            
        dim1 and dim2
            If the parameter 'tol' is not set, these two parameters have to be set. 'dim1' is the DIMINFO
            for the first geometry (the reprojected geometry column) and 'dim2' is the DIMINFO for
            the second geometry (the input geometry from the request). Values for 'dim1' and 'dim2'
            have to be SQLAlchemy expressions, either literal text (text(..)) or a select query.
            
    Note that 'tol' or 'dim1'/'dim2' only have to be set when the input geometry from the request 
    uses a different CRS than the geometry column!
    
    
    SDO_WITHIN_DISTANCE: http://download.oracle.com/docs/cd/E11882_01/appdev.112/e11830/sdo_operat.htm#i77653
    SDO_GEOM.WITHIN_DISTANCE: http://download.oracle.com/docs/cd/E11882_01/appdev.112/e11830/sdo_objgeom.htm#i856373
    DIMINFO: http://download.oracle.com/docs/cd/E11882_01/appdev.112/e11830/sdo_objrelschema.htm#i1010905
    TOLERANCE: http://download.oracle.com/docs/cd/E11882_01/appdev.112/e11830/sdo_intro.htm#i884589
    
    """
    params = additional_params.get('params', '')
    
    if isinstance(geom1, Column):
        return (func.SDO_WITHIN_DISTANCE(geom1, geom2, 
                                     'distance=%s %s' % (distance, params)) == 'TRUE')
    else:
        dim1 = additional_params.get('dim1', None)
        dim2 = additional_params.get('dim2', None)
        
        if dim1 is not None and dim2 is not None:
            return (func.SDO_GEOM.WITHIN_DISTANCE(geom1, dim1, 
                                             distance, 
                                             geom2, dim2, 
                                             params) == 'TRUE')
        else:
            tol = additional_params.get('tol', None)
            
            if tol is not None:
                return (func.SDO_GEOM.WITHIN_DISTANCE(geom1, 
                                             distance, 
                                             geom2,
                                             tol, 
                                             params) == 'TRUE')
            else:
                raise Exception('No dimension information ("dim1" and "dim2") or '\
                                'tolerance value ("tol") specified for calling '\
                                'SDO_GEOM.WITHIN_DISTANCE on Oracle, which is '\
                                'required when reprojecting.')

# 
# Copyright (C) 2009  Camptocamp
#  
# This file is part of MapFish Server
#  
# MapFish Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# MapFish Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with MapFish Server.  If not, see <http://www.gnu.org/licenses/>.
#

from mapfish.lib.filters import Filter

from geojson import loads, GeoJSON

from shapely.geometry import asShape
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

from geoalchemy import WKBSpatialElement
from geoalchemy.functions import functions

from mapfish.sqlalchemygeom import within_distance

class Spatial(Filter):
    """Spatial filter.

      type
          the type of filter to create. Possible values are
          Spatial.BOX, Spatial.WITHIN, and Spatial.GEOMETRY.

      geom_column
          the Column object corresponding to the geometry
          column (contains the database column type).

      \**kwargs
          epsg
            the EPSG code of the lon, lat or box values, see
            below.
            
          additional_params
            additional parameters used for the database function
            call (currently only used for Oracle)


          For Spatial.BOX filter:

          box
            a list of coordinates representing the bounding
            box [xmin, ymin, xmax, ymax]
            
          tolerance
            the tolerance around the box of the search
            region, is expressed in the units associated with
            the projection system of the lon/lat coordinates.
        
        
          For Spatial.WITHIN filter:

          lon
            the x coordinate of the center of the search
            region, the projection system of that coordinate
            can be specified with the epsg key.

          lat
            the y coordinate of the center of the search
            region, the projection system of that coordinate
            can be specified with the epsg key.

          tolerance
            the tolerance around the center of the search
            region, is expressed in the units associated with
            the projection system of the lon/lat coordinates.


          For Spatial.GEOMETRY filter:
            
          geometry
            the geometry to search in, formatted in a GeoJSON
            string

          tolerance
            the tolerance around the geometry of the search
            region, is expressed in the units associated with
            the projection system of the lon/lat coordinates.
            
    """

    BOX = 'BOX'
    WITHIN = 'WITHIN'
    GEOMETRY = 'GEOMETRY'

    def __init__(self, type, geom_column, **kwargs):
        self.type = type
        self.geom_column = geom_column
        self.values = kwargs
        if 'epsg' in self.values and self.values['epsg'] is not None:
            self.epsg = self.values['epsg']
        else:
            self.epsg = self.geom_column.type.srid
        self.additional_params = self.values.get('additional_params', None)

    def to_sql_expr(self):
        if self.type == self.BOX:
            geometry = self.__box_to_geometry()

        if self.type == self.WITHIN:
            geometry = Point(self.values['lon'], self.values['lat'])

        if self.type == self.GEOMETRY:
            factory = lambda ob: GeoJSON.to_instance(ob)
            geometry = loads(self.values['geometry'], object_hook=factory)
            geometry = asShape(geometry)
        
        if self.epsg != self.geom_column.type.srid:
            geom_column = functions.transform(self.geom_column, self.epsg)
        else:
            geom_column = self.geom_column

        tolerance = self.values['tolerance']
        wkb_geometry = WKBSpatialElement(buffer(geometry.wkb), self.epsg)
        
        if self.additional_params is None:
            return within_distance(geom_column, wkb_geometry, tolerance)
        else:
            return within_distance(geom_column, wkb_geometry, tolerance, self.additional_params)

    def __box_to_geometry(self):
        coords = map(float, self.values['box'])

        # define polygon from box
        point_a = (coords[0], coords[1])
        point_b = (coords[0], coords[3])
        point_c = (coords[2], coords[3])
        point_d = (coords[2], coords[1])
        point_e = point_a
        coords = (point_a, point_b, point_c, point_d, point_e)
        
        return Polygon(coords)


# 
# Copyright (C) 2007-2008  Camptocamp
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

from sqlalchemy.sql import func

from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

class Spatial(Filter):
    BOX = 'BOX'
    WITHIN = 'WITHIN'

    def __init__(self, type, geom_column, **kwargs):
        """Create a spatial filter.

          type
              the type of filter to create. Possible values are
              Spatial.BOX or Spatial.WITHIN.

          geom_column
              the Column object corresponding to the geometry
              column.

          \**kwargs
              epsg
                the EPSG code of the lon, lat or box values, see
                below.

              for Spatial.BOX filter:

              box
                a list of coordinates representing the bounding
                box [xmin, ymin, xmax, ymax]
            
              for Spatial.WITHIN filter:

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
        """
        self.type = type
        self.geom_column = geom_column
        self.values = kwargs
        if 'epsg' in self.values:
            self.epsg = self.values['epsg']
        else:
            self.epsg = None

    def to_sql_expr(self):
        if self.type == 'BOX':
            return self.__to_sql_expr_box()

        if self.type == 'WITHIN':
            return self.__to_sql_expr_within()

    def __to_sql_expr_box(self):
        coords = self.values['box']

        epsg = self.geom_column.type.srid
        if self.epsg is not None:
            epsg = self.epsg

        coords = map(float, coords)

        # define polygon from box
        point_a = (coords[0], coords[1])
        point_b = (coords[0], coords[3])
        point_c = (coords[2], coords[3])
        point_d = (coords[2], coords[1])
        point_e = point_a
        coords = (point_a, point_b, point_c, point_d, point_e)
        poly = Polygon(coords)
        pg_poly = func.geomfromtext(poly.wkt, epsg)

        if epsg != self.geom_column.type.srid:
            pg_poly = func.transform(pg_poly, epsg)

        # TODO : use st_intersects when only postgis 1.3 supported
        return self.geom_column.op('&&')(pg_poly) and \
            func.intersects(self.geom_column, pg_poly)

    def __to_sql_expr_within(self):
        lon = self.values['lon']
        lat = self.values['lat']
        tolerance = self.values['tolerance']

        epsg = self.geom_column.type.srid
        if self.epsg is not None:
            epsg = self.epsg

        point = Point(lon, lat)
        pg_point = func.pointfromtext(point.wkt, epsg)

        geom = self.geom_column
        if epsg != self.geom_column.type.srid:
            geom = func.transform(geom, epsg)
        
        # TODO : use st_dwithin when only Postgis 1.3 supported
        if tolerance is not None and tolerance > 0:
            e = func.expand(geom, tolerance).op('&&')(pg_point) and \
                (func.distance(geom, pg_point) < tolerance)
        else:
            e = func.within(pg_point, geom)

        return e

# 
# Copyright (C) 2007  Camptocamp
#  
# This file is part of CartoWeb
#  
# ClownFish is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#


from sqlalchemy.sql import select
from sqlalchemy.sql import and_
from sqlalchemy.sql import func

from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

class Search:
    EPSG = 4326
    UNITS = 'degrees'

    def __init__(self, idColumn, geomColumn, epsg=EPSG, units=UNITS):
        self.idColumn = idColumn
        self.geomColumn = geomColumn
        self.epsg = epsg
        self.units = units
        self.limit = None
    
    def buildExpression(self, request):
        id = None
        path = request.path_info.split("/")
        if len(path) > 1:
            path_pieces = path[-1].split(".")
            if len(path_pieces) > 1 and path_pieces[0].isdigit():
                id = int(path_pieces[0])

        expr = None
        if id is not None:
            expr = self.idColumn == id;
        
        if 'maxfeatures' in request.params:
            self.limit = int(request.params['maxfeatures'])
        
        epsg = self.EPSG
        if 'epsg' in request.params:
            epsg = request.params['epsg']

        # deal with lonlat query
        if 'lon' in request.params and 'lat' in request.params and 'radius' in request.params:
            # define point from lonlat
            lon = float(request.params['lon'])
            lat = float(request.params['lat'])
            point = Point(lon, lat)
            pgPoint = func.pointfromtext(point.wkt, epsg)

            if epsg != self.epsg:
                pgPoint = func.transform(pgPoint, self.epsg)

            # build query expression
            if self.units == 'degrees':
                dist = func.distance_sphere(self.geomColumn, pgPoint)
            else:
                dist = func.distance(self.geomColumn, pgPoint)
            e = dist < float(request.params['radius'])

            # update query expression
            if expr is not None:
                expr = and_(expr, e)
            else:
                expr = e

        # deal with box query
        elif 'box' in request.params:
            coords = request.params['box'].split(',')
            # define polygon from box
            pointA = (float(coords[0]), float(coords[1]))
            pointB = (float(coords[0]), float(coords[3]))
            pointC = (float(coords[2]), float(coords[3]))
            pointD = (float(coords[2]), float(coords[1]))
            pointE = pointA
            coords = (pointA, pointB, pointC, pointD, pointE)
            poly = Polygon(coords)
            pgPoly = func.geomfromtext(poly.wkt, epsg)

            if epsg != self.epsg:
                pgPoly =  func.transform(pgPoly, self.epsg)

            # build query expression
            e = self.geomColumn.op('&&')(pgPoly)

            # update query expression
            if expr is not None:
                expr = and_(expr, e)
            else:
                expr = e

        return expr

    def query(self, session, obj, tableObj, expr):
        return session.query(obj).from_statement(
            select([tableObj], expr).limit(self.limit)).all()

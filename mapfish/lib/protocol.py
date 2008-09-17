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

import logging
log = logging.getLogger(__name__)

import decimal

from shapely.geometry import asShape

from sqlalchemy.sql import select

from geojson import dumps as _dumps, loads, Feature, FeatureCollection, GeoJSON
from geojson.codec import PyGFPEncoder

from mapfish.lib.filters.spatial import Spatial

class MapFishJSONEncoder(PyGFPEncoder):
    """ SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    for numeric columns. simplejson does not know how to deal with
    objects of that type. This class provides a simple encoder that
    can deal with decimal.Decimal objects. """

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return PyGFPEncoder.default(self, obj)

def dumps(obj, cls=MapFishJSONEncoder, **kwargs):
    """ Wrapper for geojson's dumps function """
    return _dumps(obj, cls=cls, **kwargs)

def create_default_filter(request, id_column, geom_column):
    """Create MapFish default filter based on the request params. It
    is either a box or within spatial filter, depending on the request
    params."""

    filter = None

    # get projection EPSG code
    epsg = None
    if 'epsg' in request.params:
        epsg = int(request.params['epsg'])

    if 'box' in request.params:
        # box filter
        filter = Spatial(
            Spatial.BOX,
            geom_column,
            box=request.params['box'].split(','),
            epsg=epsg
        )
    elif 'lon' and 'lat' and 'tolerance' in request.params:
        # within filter
        filter = Spatial(
            Spatial.WITHIN,
            geom_column,
            lon=float(request.params['lon']),
            lat=float(request.params['lat']),
            tolerance=float(request.params['tolerance']),
            epsg=epsg
        )

    return filter

class Protocol(object):

    def __init__(self, Session, mapped_class, readonly=False):
        self.Session = Session
        self.mapped_class = mapped_class
        self.readonly = readonly

    def _query(self, filter=None, limit=None):
        """ Query the database using the passed filter and return
            instances of the mapped class. """
        if filter:
            filter = filter.to_sql_expr()
        # 0 indicates the offset and is mandatory for SA to create the limit
        # in the SQL
        return self.Session.query(self.mapped_class).filter(filter)[0:limit]

    def _encode(self, objects):
        """ Return a GeoJSON representation of the passed objects. """
        if objects:
            if isinstance(objects, list):
                return dumps(
                    FeatureCollection(
                        [o.toFeature() for o in objects if o.geometry]
                    )
                )
            else:
                return dumps(objects.toFeature())

    def index(self, request, response, format='json', filter=None):
        """ Build a query based on the filter and the request
        params, send the query to the database, and return a
        GeoJSON representation of the results. """

        # only json is supported
        if format != 'json':
            response.status_code = 404
            return

        limit = None
        if 'maxfeatures' in request.params:
            limit = int(request.params['maxfeatures'])

        if not filter:
            # create MapFish default filter
            filter = create_default_filter(
                request,
                self.mapped_class.primary_key_column(),
                self.mapped_class.geometry_column()
            )

        return self._encode(self._query(filter, limit))

    def show(self, request, response, id, format='json'):
        """ Build a query based on the id argument, send the query
        to the database, and return a GeoJSON representation of the
        result. """

        # only json is supported
        if format != 'json':
            response.status_code = 404
            return

        return self._encode(self.Session.query(self.mapped_class).get(id))

    def create(self, request, response):
        """ Read the GeoJSON feature collection from the request body and
            create new objects in the database. """
        if self.readonly:
            response.status_code = 403
            return
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        collection = loads(content, object_hook=factory)
        if not isinstance(collection, FeatureCollection):
            response.status_code = 400
            return
        objects = []
        for feature in collection.features:
            create = False
            obj = None
            if isinstance(feature.id, int):
                obj = self.Session.query(self.mapped_class).get(feature.id)
            if obj is None:
                obj = self.mapped_class()
                obj.geometry = asShape(feature.geometry)
                create = True
            for key in feature.properties:
                obj[key] = feature.properties[key]
            if create:
                self.Session.save(obj)
            objects.append(obj)
        self.Session.commit()
        response.status_code = 201
        if len(objects) > 0:
            return dumps(FeatureCollection([o.toFeature() for o in objects]))
        return

    def update(self, request, response, id):
        """ Read the GeoJSON feature from the request body and update the
        corresponding object in the database. """
        if self.readonly:
            response.status_code = 403
            return
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            response.status_code = 404
            return
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        feature = loads(content, object_hook=factory)
        if not isinstance(feature, Feature):
            response.status_code = 400
            return response
        obj.geometry = asShape(feature.geometry)
        for key in feature.properties:
            obj[key] = feature.properties[key]
        self.Session.commit()
        response.status_code = 201
        return dumps(obj.toFeature())

    def delete(self, request, response, id):
        """ Remove the targetted feature from the database """
        if self.readonly:
            response.status_code = 403
            return
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            response.status_code = 404
            return
        self.Session.delete(obj)
        self.Session.commit()
        response.status_code = 204
        return


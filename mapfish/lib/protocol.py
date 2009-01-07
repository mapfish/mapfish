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

import decimal, datetime

from shapely.geometry import asShape

from sqlalchemy.sql import select, asc, desc

from geojson import dumps as _dumps, loads, Feature, FeatureCollection, GeoJSON
from geojson.codec import PyGFPEncoder

from mapfish.lib.filters.spatial import Spatial

class MapFishJSONEncoder(PyGFPEncoder):
    """ SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    for numeric columns and datetime.date for dates. simplejson does
    not know how to deal with objects of those types. This class provides
    a simple encoder that can deal with these kinds of objects. """

    def default(self, obj):
        if isinstance(obj, (decimal.Decimal, datetime.date, datetime.datetime)):
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
    elif 'lon' and 'lat' in request.params:
        # within filter
        tolerance = None
        if 'tolerance' in request.params:
            tolerance = float(request.params['tolerance'])
        filter = Spatial(
            Spatial.WITHIN,
            geom_column,
            lon=float(request.params['lon']),
            lat=float(request.params['lat']),
            tolerance=tolerance,
            epsg=epsg
        )

    return filter

class Protocol(object):

    def __init__(self, Session, mapped_class, readonly=False, **kwargs):
        self.Session = Session
        self.mapped_class = mapped_class
        self.readonly = readonly
        self.before_create = None
        if kwargs.has_key('before_create'):
            self.before_create = kwargs['before_create']
        self.before_update = None
        if kwargs.has_key('before_update'):
            self.before_update = kwargs['before_update']

    def _query(self, filter=None, limit=None, offset=None, order_by=None):
        """ Query the database using the passed limit, offset and filter,
            and return instances of the mapped class. """
        if filter:
            filter = filter.to_sql_expr()
        query = self.Session.query(self.mapped_class).filter(filter)
        if order_by:
            query = query.order_by(order_by)
        query = query.limit(limit).offset(offset)
        return query.all()

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

    def _get_default_filter(self, request):
        """ Return a MapFish default filter. """
        return create_default_filter(
            request,
            self.mapped_class.primary_key_column(),
            self.mapped_class.geometry_column()
        )

    def _get_order_by(self, request):
        """ Return an SA order_by """
        column_name = None
        if 'sort' in request.params:
            column_name = request.params['sort']
        elif 'order_by' in request.params:
            column_name = request.params['order_by']
            
        if column_name and column_name in self.mapped_class.__table__.c:
            column = self.mapped_class.__table__.c[column_name]
            if 'dir' in request.params and request.params['dir'].upper() == 'DESC':
                return desc(column)
            else: 
                return asc(column)
        else:
            return None

    def index(self, request, response, format='json', filter=None):
        """ Build a query based on the filter and the request
        params, send the query to the database, and return a
        GeoJSON representation of the results. """

        # only json is supported
        if format != 'json':
            response.status_code = 404
            return

        limit = None
        offset = None

        if 'maxfeatures' in request.params:
            limit = int(request.params['maxfeatures'])
        if 'limit' in request.params:
            limit = int(request.params['limit'])
        if 'offset' in request.params:
            offset = int(request.params['offset'])

        if not filter:
            # create MapFish default filter
            filter = self._get_default_filter(request)

        order_by = self._get_order_by(request)
            
        return self._encode(self._query(filter, limit, offset, order_by))

    def count(self, request, filter=None):
        """ Return the number of records matching the given filter. """
        if not filter:
            filter = self._get_default_filter(request)
        if filter:
            filter = filter.to_sql_expr()
        return str(self.Session.query(self.mapped_class).filter(filter).count())

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
            if self.before_create is not None:
                self.before_create(request, feature)
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
        if self.before_update is not None:
            self.before_update(request, feature)
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


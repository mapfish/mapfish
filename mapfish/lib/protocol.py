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

import logging
log = logging.getLogger(__name__)

import decimal, datetime

from pylons.controllers.util import abort

from shapely.geometry import asShape

from sqlalchemy.sql import select, asc, desc

from geojson import dumps as _dumps, loads, Feature, FeatureCollection, GeoJSON
from geojson.codec import PyGFPEncoder

from mapfish.lib.filters import Filter
from mapfish.lib.filters.spatial import Spatial
from mapfish.lib.filters.comparison import Comparison
from mapfish.lib.filters.logical import Logical


PARAM_TO_FILTER_TYPE = {
    "eq": Comparison.EQUAL_TO,
    "ne": Comparison.NOT_EQUAL_TO,
    "lt": Comparison.LOWER_THAN,
    "lte": Comparison.LOWER_THAN_OR_EQUAL_TO,
    "gt": Comparison.GREATER_THAN,
    "gte": Comparison.GREATER_THAN_OR_EQUAL_TO,
    "like": Comparison.LIKE,
    "ilike": Comparison.ILIKE
}

class MapFishJSONEncoder(PyGFPEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. simplejson does
    # not know how to deal with objects of those types. This class provides
    # a simple encoder that can deal with these kinds of objects.

    def default(self, obj):
        if isinstance(obj, (decimal.Decimal, datetime.date, datetime.datetime)):
            return str(obj)
        return PyGFPEncoder.default(self, obj)

def dumps(obj, cls=MapFishJSONEncoder, **kwargs):
    # Wrapper for geojson's dumps function.
    return _dumps(obj, cls=cls, **kwargs)

def create_geom_filter(request, mapped_class):
    """Create MapFish geometry filter based on the request params. Either
    a box or within or geometry filter, depending on the request params."""

    geom_column = mapped_class.geometry_column()

    filter = None
    tolerance = 0
    if 'tolerance' in request.params:
        tolerance = float(request.params['tolerance'])

    # get projection EPSG code
    epsg = None
    if 'epsg' in request.params:
        epsg = int(request.params['epsg'])

    # "box" is an alias to "bbox"
    box = None
    if 'bbox' in request.params:
        box = request.params['bbox']
    elif 'box' in request.params:
        box = request.params['box']

    if box is not None:
        # box spatial filter
        filter = Spatial(
            Spatial.BOX,
            geom_column,
            box=box.split(','),
            tolerance=tolerance,
            epsg=epsg
        )
    elif 'lon' and 'lat' in request.params:
        # within spatial filter
        filter = Spatial(
            Spatial.WITHIN,
            geom_column,
            lon=float(request.params['lon']),
            lat=float(request.params['lat']),
            tolerance=tolerance,
            epsg=epsg
        )
    elif 'geometry' in request.params:
        # geometry spatial filter
        filter = Spatial(
            Spatial.GEOMETRY,
            geom_column,
            geometry=request.params['geometry'],
            tolerance=tolerance,
            epsg=epsg
        )
    return filter

def create_attr_filter(request, mapped_class):
    """Create MapFish attribute filter based on the request params,
    either a comparison filter or a set of comparison filters within
    a logical and filter."""

    filter = None
    if 'queryable' in request.params:
        # comparison filter
        queryable = request.params['queryable'].split(',')
        for k in request.params:
            if len(request.params[k]) <= 0:
                continue
            if "__" not in k:
                continue
            col, op = k.split("__")
            if col not in queryable or op not in PARAM_TO_FILTER_TYPE:
                continue
            type = PARAM_TO_FILTER_TYPE[op]
            f = Comparison(
                type,
                mapped_class.__table__.columns[col],
                value=request.params[k]
            )
            if filter is None:
                filter = f
            else:
                filter = Logical(
                    Logical.AND,
                    filters=[filter, f]
                )
    return filter

def create_default_filter(request, mapped_class):
    """ Create MapFish default filter based on the request params."""

    geom_filter = create_geom_filter(request, mapped_class) 
    attr_filter = create_attr_filter(request, mapped_class)

    if geom_filter is None and attr_filter is None:
        return None

    return Logical(
        Logical.AND,
        filters=[geom_filter, attr_filter]
    )

def asbool(val):
    # Convert the passed value to a boolean.
    if isinstance(val, str) or isinstance(val, unicode):
        low = val.lower()
        return low != 'false' and low != '0'
    else:
        return bool(val)   

class Protocol(object):
    """ Protocol class.

      Session
          the SQLAlchemy session.

      mapped_class
          the class mapped to a database table in the ORM.

      readonly
          ``True`` if this protocol is read-only, ``False`` otherwise. If
          ``True``, the methods ``create()``, ``update()`` and  ``delete()``
          will set 403 as the response status and return right away.

      \**kwargs
          before_create
            a callback function called before a feature is inserted
            in the database table, the function receives the request
            and the feature about to be inserted.

          before_update
            a callback function called before a feature is updated
            in the database table, the function receives the request
            and the feature about to be updated.
    """

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

    def _encode(self, objects, request, response):
        """ Return a GeoJSON representation of the passed objects. """
        if objects is not None:
            response.content_type = "application/json"
            if isinstance(objects, list):
                return dumps(
                    FeatureCollection(
                        [self._filter_attrs(o.toFeature(), request) for o in objects if o.geometry]
                    )
                )
            else:
                return dumps(self._filter_attrs(objects.toFeature(), request))

    def _filter_attrs(self, feature, request):
        """ Remove some attributes from the feature and set the geometry to None
            in the feature based ``attrs`` and the ``no_geom`` parameters. """
        if 'attrs' in request.params:
            attrs = request.params['attrs'].split(',')
            props = feature.properties
            new_props = {}
            for name in attrs:
                if name in props:
                    new_props[name] = props[name]
            feature.properties = new_props

        if asbool(request.params.get('no_geom', False)):
            feature.geometry=None
        return feature

    def _get_default_filter(self, request):
        """ Return a MapFish default filter. """
        return create_default_filter(
            request, self.mapped_class
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

    def _query(self, request, filter=None, execute=True):
        """ Build a query based on the filter and the request params,
            and send the query to the database. """

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

        if filter and isinstance(filter, Filter):
            filter = filter.to_sql_expr()

        query = self.Session.query(self.mapped_class).filter(filter)

        order_by = self._get_order_by(request)
        if order_by:
            query = query.order_by(order_by)

        query = query.limit(limit).offset(offset)

        if execute:
            return query.all()
        else:
            return query

    def index(self, request, response, format='json', filter=None):
        """ Build a query based on the filter and the request
        params, send the query to the database, and return a
        GeoJSON representation of the query results. """

        # only json is supported
        if format != 'json':
            abort(404)

        return self._encode(self._query(request, filter), request, response)

    def count(self, request, filter=None):
        """ Return the number of records matching the given filter. """
        if not filter:
            filter = self._get_default_filter(request)
        if filter and isinstance(filter, Filter):
            filter = filter.to_sql_expr()
        return str(self.Session.query(self.mapped_class).filter(filter).count())

    def show(self, request, response, id, format='json'):
        """ Build a query based on the id argument, send the query
        to the database, and return a GeoJSON representation of the
        result. """

        # only json is supported
        if format != 'json':
            abort(404)

        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            abort(404)

        return self._encode(obj, request, response)

    def create(self, request, response, execute=True):
        """ Read the GeoJSON feature collection from the request body and
            create new objects in the database. """
        if self.readonly:
            abort(403)
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        collection = loads(content, object_hook=factory)
        if not isinstance(collection, FeatureCollection):
            abort(400)
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
                create = True
            obj.geometry = asShape(feature.geometry)
            for key in feature.properties:
                obj[key] = feature.properties[key]
            if create:
                self.Session.add(obj)
            objects.append(obj)
        if execute:
            self.Session.commit()
        response.status = 201
        if len(objects) > 0:
            return self._encode(objects, request, response)
        return

    def update(self, request, response, id):
        """ Read the GeoJSON feature from the request body and update the
        corresponding object in the database. """
        if self.readonly:
            abort(403)
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            abort(404)
        content = request.environ['wsgi.input'].read(int(request.environ['CONTENT_LENGTH']))
        factory = lambda ob: GeoJSON.to_instance(ob)
        feature = loads(content, object_hook=factory)
        if not isinstance(feature, Feature):
            abort(400)
        if self.before_update is not None:
            self.before_update(request, feature)
        obj.geometry = asShape(feature.geometry)
        for key in feature.properties:
            obj[key] = feature.properties[key]
        self.Session.commit()
        response.status = 201
        return self._encode(obj, request, response)

    def delete(self, request, response, id):
        """ Remove the targetted feature from the database """
        if self.readonly:
            abort(403)
        obj = self.Session.query(self.mapped_class).get(id)
        if obj is None:
            abort(404)
        self.Session.delete(obj)
        self.Session.commit()
        response.status = 204
        return


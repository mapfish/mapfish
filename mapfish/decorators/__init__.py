import logging
import warnings
import decimal, datetime

from decorator import decorator

import simplejson

from pylons.decorators.util import get_pylons

from geojson.codec import PyGFPEncoder as GeoJSONEncoder


log = logging.getLogger(__name__)

class MapFishEncoder(GeoJSONEncoder):
    # SQLAlchemy's Reflecting Tables mechanism uses decimal.Decimal
    # for numeric columns and datetime.date for dates. simplejson does
    # not know how to deal with objects of those types. This class provides
    # a simple encoder that can deal with these kinds of objects.

    def default(self, obj):
        if isinstance(obj, (decimal.Decimal, datetime.date, datetime.datetime)):
            return str(obj)
        return GeoJSONEncoder.default(self, obj)

# _jsonify shouldn't be part of MapFish. It should be in Pylons.
# See <http://pylonshq.com/project/pylonshq/ticket/632>
def _jsonify(cb=None, **dumps_kwargs):
    def wrapper(func, *args, **kwargs):
        pylons = get_pylons(args)
        cb_name = pylons.request.params.get(cb)
        if cb_name is not None:
            pylons.response.headers['Content-Type'] = 'text/javascript'
        else:
            pylons.response.headers['Content-Type'] = 'application/json'
        data = func(*args, **kwargs)
        output = simplejson.dumps(data, **dumps_kwargs)
        if cb_name is not None:
            output = str(cb_name) + '(' + output + ');'
            log.debug("Returning JS wrapped action output")
        else:
            if isinstance(data, (list, tuple)):
                msg = "JSON responses with Array envelopes are susceptible to " \
                      "cross-site data leak attacks, see " \
                      "http://pylonshq.com/warnings/JSONArray"
                warnings.warn(msg, Warning, 2)
                log.warning(msg)
            log.debug("Returning JSON wrapped action output")
        return output
    return decorator(wrapper)

geojsonify = _jsonify(cls=MapFishEncoder)

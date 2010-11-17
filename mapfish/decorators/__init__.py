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

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

""" The ``mapfish.lib.filters`` module. This module's sub-modules include
filter implementations.

Filters are commonly created in the ``index()`` action of MapFish controllers
and passed to the ``protocol`` instance through the ``filter`` positional
argument of the protocol ``index()`` method.

Example::

      class CountriesController(BaseController):
          readonly = True # if set to True, only GET is supported

          def __init__(self):
              self.protocol = Protocol(Session, Country, self.readonly)

          def index(self, format='json'):
              # complement the MapFish default filter so only features
              # in the [5, 45, 6, 50] extent are returned
              filters = [
                  create_default_filter(request, Country),
                  Spatial(
                      Spatial.BOX,
                      Country.geometry_column(),
                      box=[5, 45, 6, 50]
                  )
              ]
              filter = Logical(Logical.AND, filters=filters)
              return self.protocol.index(request, response, format=format, filter=filter)

"""

__all__ = ['comparison', 'featureid', 'logical', 'spatial']

class Filter(object):

    """Base filter classe. Filters implemented in submodules of the
    ``mapfish.lib.filters`` module inherit from this class. Filter subclasses
    implement the ``to_sql_expr()`` method, this method returns an SQLAlchemy
    filter expression.

    """
    def __init__(self):
        raise NotImplementedError('Filter cannot be instantiated')

    def to_sql_expr(self):
        raise NotImplementedError('to_sql_expr must be implemented')

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

from sqlalchemy.sql import and_, or_, not_

class Logical(Filter):
    """Logical filter.

      type
          the type of filter to create. Possible values are Logical.NOT,
          Logical.AND or Logical.OR.

      filters=None
          a list of filters this filter will create logical expressions
          with. filters can also be added after the creation of the 
          logical filter, using logical_filter.filters.append(filter).
    """

    NOT = '!'
    AND = '&&'
    OR  = '||'

    def __init__(self, type, filters=None):
        self.type = type
        if filters is None:
            self.filters = []
        else:
            self.filters = filters

    def to_sql_expr(self):
        """Return the SQLAlchemy SQL expression corresponding to that filter.
        """

        if len(self.filters) == 0:
            return None

        if self.type == Logical.NOT:
            ret = None
            if self.filters[0]:
                ret = not_(self.filters[0].to_sql_expr())
            return ret

        if len(self.filters) < 2:
            ret = None
            if self.filters[0]:
                ret = self.filters[0].to_sql_expr()
            return ret

        assert len(self.filters) > 1

        if self.type == Logical.AND:
            return and_(*[f.to_sql_expr() for f in self.filters if f])

        if self.type == Logical.OR:
            return or_(*[f.to_sql_expr() for f in self.filters if f])

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

from sqlalchemy.sql import and_

class Comparison(Filter):
    """Comparison filter

      type
          the type of filter to create. Possible values are:
            Comparison.EQUAL_TO

            Comparison.NOT_EQUAL_TO

            Comparison.LOWER_THAN

            Comparison.LOWER_THAN_OR_EQUAL_TO

            Comparison.GREATER_THAN

            Comparison.GREATER_THAN_OR_EQUAL_TO

            Comparison.BETWEEN

            Comparison.LIKE

            Comparison.ILIKE

      column
          the column to use for the comparison. 

      \**kwargs
          lower_bound
            the lower bound value, to be used with the BETWEEN type.

          upper_bound
            the upper bound value, to be used with the BETWEEN type.

          value
            the value to use.
    """

    EQUAL_TO = '=='
    NOT_EQUAL_TO = '!='
    LOWER_THAN = '<'
    LOWER_THAN_OR_EQUAL_TO = '<='
    GREATER_THAN = '>'
    GREATER_THAN_OR_EQUAL_TO = '>='
    BETWEEN = '..'
    LIKE = '~'
    ILIKE = '~~'

    def __init__(self, type, column, **kwargs):
        self.type = type
        self.column = column
        self.values = kwargs

    def to_sql_expr(self):
        """Return the SQLAlchemy SQL expression corresponding to that filter.
        """
        if self.type == Comparison.EQUAL_TO:
            return self.column == self.values['value']

        if self.type == Comparison.NOT_EQUAL_TO:
            return self.column != self.values['value']

        if self.type == Comparison.LOWER_THAN:
            return self.column < self.values['value']

        if self.type == Comparison.LOWER_THAN_OR_EQUAL_TO:
            return self.column <= self.values['value']

        if self.type == Comparison.GREATER_THAN:
            return self.column > self.values['value']

        if self.type == Comparison.GREATER_THAN_OR_EQUAL_TO:
            return self.column >= self.values['value']

        if self.type == Comparison.BETWEEN:
            return and_(
                self.column <= self.values['upper_bound'],
                self.column >= self.values['lower_bound']
            )

        if self.type == Comparison.LIKE:
            return self.column.like(self.values['value'])

        if self.type == Comparison.ILIKE:
            return self.column.ilike(self.values['value'])

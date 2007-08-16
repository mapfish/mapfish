"""
SQLAlchemy geometry type support
see: http://www.sqlalchemy.org/docs/types.html#types_custom

  Example
  -------
from sqlalchemy import *
from sqlalchemygeom import Geometry

# see: http://www.sqlalchemy.org/docs/dbengine.html
db = create_engine('postgres://www-data:www-data@kirishima.c2c:5433/epfl')

metadata = MetaData()
metadata.connect(db)

wifi_t = Table('wifi', metadata,
               Column('gid', Integer, primary_key=True),
               # add more columns here ...
               Column('the_geom', Geometry)
               )

# basic select
r = wifi_t.select(wifi_t.c.gid == 10).execute()
w = r.fetchone()
print w.the_geom

# advanced select
from shapely.geometry.point import Point
from binascii import b2a_hex
me = Point(532778, 152205)

r = wifi_t.select(metadata.engine.func.distance(wifi_t.c.the_geom, b2a_hex(me.wkb)) < 100).execute()
print [(i.gid, i.the_geom.distance(me)) for i in r]

## update
#u = wifi_t.update(wifi_t.c.gid == 10)
#w.the_geom.y += 9.0
#u.execute(the_geom = w.the_geom)
"""

from sqlalchemy.types import TypeEngine
from shapely.wkb import loads
from binascii import a2b_hex, b2a_hex

class Geometry(TypeEngine):

    def compare_values(self, x, y):
        return x.equals(y)

    def convert_bind_param(self, value, engine):
        """convert value from a geometry object to database"""
        return b2a_hex(value.wkb)

    def convert_result_value(self, value, engine):
        """convert value from database to a geometry object"""
        if value is not None:
            return loads(a2b_hex(value))
        else:
            return None

# 
# Copyright (C) 2007  Camptocamp
#  
# This file is part of MapFish
#  
# MapFish is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# MapFish is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with MapFish.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Feature class implementing the Python Geo Interface
See http://trac.gispython.org/projects/PCL/wiki/PythonGeoInterface

Objects of this class can be serialized to GeoJSON using PCL's
GeoJSON dump call.

See http://trac.gispython.org/projects/PCL/browser/GeoJSON
"""

class Feature(object):
    def __init__(self, id, geometry, **props):
        self.id = id
        self.geometry = geometry
        self.properties = {}
        for key, value in props.items():
            self.properties[key] = value

    @property
    def __geo_interface__(self):
        return {'id': self.id,
                'geometry': self.geometry,
                'properties': self.properties}

class FeatureCollection(list):
    @property
    def __geo_interface__(self):
        return {'features': self}


if __name__ == '__main__':
    import geojson
    from shapely.geometry import Point

    f = Feature(12, Point(9, 5), foo='bar')
    assert(geojson.issupported(f))

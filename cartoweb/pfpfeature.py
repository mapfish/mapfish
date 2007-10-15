# 
# Copyright (C) 2007  Camptocamp
#  
# This file is part of CartoWeb
#  
# CartoWeb is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# CartoWeb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with CartoWeb.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Feature class implementing the Python Feature Protocol.
See http://trac.gispython.org/projects/PCL/wiki/PythonFeatureProtocol

Objects of this class can be serialized to GeoJSON using PCL's
GeoJSON dump call.

See http://trac.gispython.org/projects/PCL/browser/GeoJSON
    http://trac.gispython.org/projects/PCL/wiki/PythonGeoInterface
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

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

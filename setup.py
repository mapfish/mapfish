# 
# Copyright (C) 2007-2008  Camptocamp
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

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name                 = 'MapFish',
      version              = '0.3',
      license              = 'LGPLv3',
      install_requires     = ['SQLAlchemy >= 0.4.6',
                              'Pylons >= 0.9.6.1',
                              'Shapely >= 1.0a7',
                              'GeoJSON >= 1.0a3'],
      zip_safe             = False,
      include_package_data = True,
      packages             = find_packages(),
      classifiers          = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        ],
      entry_points         = """
        [paste.paster_create_template]
        mapfish = mapfish.util:MapFishTemplate
        [paste.paster_command]
        mf-controller = mapfish.commands:MapFishControllerCommand
        mf-model = mapfish.commands:MapFishModelCommand
        mf-layer = mapfish.commands:MapFishLayerCommand
        """
)

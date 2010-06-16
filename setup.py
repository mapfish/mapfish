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

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys

requirements = ['SQLAlchemy>=0.6.1,<=0.6.99',
                'Pylons>=0.9.7,<=0.9.7.99',
                'geojson>=1.0,<=1.0.99',
                'GeoAlchemy>=0.3,<=0.3.99']

# Shapely and Psychopg2 cannot be installed on Windows via python eggs
if sys.platform != 'win32':
    requirements.append('Shapely>=1.0.7,<=1.0.99')
    requirements.append('psycopg2>=2.0.10,<=2.0.99')

# add dependency on ctypes only for python < 2.5 wich does not embed ctypes
if sys.version_info < (2, 5):
    requirements.append('ctypes')


setup(name                 = 'mapfish',
      version              = '2.0dev',
      license              = 'LGPLv3',
      install_requires     = requirements,
      zip_safe             = False,
      include_package_data = True,
      packages             = find_packages(),
      keywords             = 'pylons wsgi framework sqlalchemy geojson shapely GIS',
      author               = 'Camptocamp',
      url                  = 'http://www.mapfish.org',
      description          = 'The MapFish web-mapping framework.',
      classifiers          = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Pylons',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
      entry_points         = """
        [paste.paster_create_template]
        mapfish = mapfish.util:MapFishTemplate
        [paste.paster_command]
        mf-controller = mapfish.commands:MapFishControllerCommand
        mf-model = mapfish.commands:MapFishModelCommand
        mf-layer = mapfish.commands:MapFishLayerCommand
        """,
      long_description      = """
      MapFish
      =======

      MapFish is a Pylons-based web framework with GIS orientations.

      MapFish provides:

        * a geometry type which is to be used when mapping PostGIS tables
          with SQLAlchemy

        * a paster command to generate model and controller mode
          corresponding to layers (PostGIS tables) defined in a 
          configuration file

        * an implementation of a RESTful protocols for creating, reading,
          updating, and deleting geographic objects (features)

      MapFish relies on the geojson and shapely packages, see
      http://gispython.org.

      MapFish projects are Pylons projects, the project developer
      therefore fully benefits from the power of Pylons and its
      companion components (SQLAlchemy, Mako, etc.).

      Current status
      --------------

      MapFish 2.0dev described in this page is the current stable version.

      Download and Installation
      -------------------------

      MapFish can be installed with `Easy Install
      <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ by typing::

          > easy_install mapfish
      """
)

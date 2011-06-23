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

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys

requirements = ['SQLAlchemy>=0.6.1',
                'Pylons>=1.0',
                'geojson>=1.0',
                'GeoAlchemy>=0.5']

# Shapely and Psychopg2 cannot be installed on Windows via python eggs
if sys.platform != 'win32':
    requirements.append('Shapely>=1.2')

# add dependency on ctypes only for python < 2.5 wich does not embed ctypes
if sys.version_info < (2, 5):
    requirements.append('ctypes')


setup(name                 = 'mapfish',
      version              = '2.2',
      license              = 'Modified BSD',
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
        'License :: OSI Approved :: BSD License',
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

      MapFish 2.2 described in this page is the current stable version.

      Download and Installation
      -------------------------

      MapFish can be installed with `Easy Install
      <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ by typing::

          > easy_install mapfish
      """
)

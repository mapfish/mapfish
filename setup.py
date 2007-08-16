from setuptools import setup

setup(name             = 'CartoWeb',
      version          = '0.0',
      license          = 'GPL',
      install_requires = ['SQLAlchemy >= 0.3',
                          'Shapely',
                          'GeoJSON'],
      dependency_links = ["http://dev.camptocamp.com/packages/eggs/"],
      zip_safe         = True,
      packages         = ['cartoweb', 'cartoweb.plugins'],
      classifiers      = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        ],
)


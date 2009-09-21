#!/usr/bin/env python
"""Generate go-mapfish-framework.py"""
import sys
import textwrap
import virtualenv


after_install = """\
import os, subprocess
def after_install(options, home_dir):
    etc = join(home_dir, 'etc')
    ## TODO: this should all come from distutils
    ## like distutils.sysconfig.get_python_inc()
    if sys.platform == 'win32':
        lib_dir = join(home_dir, 'Lib')
        bin_dir = join(home_dir, 'Scripts')
    elif is_jython:
        lib_dir = join(home_dir, 'Lib')
        bin_dir = join(home_dir, 'bin')
    else:
        lib_dir = join(home_dir, 'lib', py_version)
        bin_dir = join(home_dir, 'bin')

    if not os.path.exists(etc):
        os.makedirs(etc)
    # install mapfish egg
    subprocess.call([join(bin_dir, 'easy_install'),
        '--index-url', 'http://www.mapfish.org/downloads/%s/pkg',
        '--allow-hosts', 'www.mapfish.org',
        'mapfish'])
    # install mapfish.plugin.client egg
    subprocess.call([join(bin_dir, 'easy_install'),
        '--index-url', 'http://www.mapfish.org/downloads/%s/pkg',
        '--allow-hosts', 'www.mapfish.org',
        'mapfish.plugin.client'])

    if sys.platform == 'win32':
        import urllib2, cStringIO, zipfile
        try:
            # installation of psycopg2 for windows:
            url = 'http://www.mapfish.org/downloads/exe/psycopg2-2.0.10.win32-py2.5-pg8.3.7-release.exe'
            print >> sys.stdout, '\\nDownloading ' + url
            remotezip = urllib2.urlopen(url)
            zipinmemory = cStringIO.StringIO(remotezip.read())
            print >> sys.stdout, 'Processing psycopg2 installation for windows'
            zip = zipfile.ZipFile(zipinmemory)
            for fn in zip.namelist():
                fn_splitted = fn.split('/')[1:] # remove PLATLIB dir
                fn_path = os.path.join(lib_dir, 'site-packages', *fn_splitted)
                if not os.path.exists(os.path.dirname(fn_path)):
                    os.makedirs(os.path.dirname(fn_path))
                f = open(fn_path, 'wb')
                f.write(zip.read(fn))
                f.close()
            print >> sys.stdout, 'Installed ' \\
                     + os.path.abspath(os.path.join(lib_dir,
                                                    'site-packages',
                                                    'psycopg2'))

            # installation of shapely for windows:
            url = 'http://www.mapfish.org/downloads/exe/Shapely-1.0.12.win32.exe'
            print >> sys.stdout, '\\nDownloading ' + url
            remotezip = urllib2.urlopen(url)
            zipinmemory = cStringIO.StringIO(remotezip.read())
            print >> sys.stdout, 'Processing shapely installation for windows'
            zip = zipfile.ZipFile(zipinmemory)

            for fn in zip.namelist():
                fn_splitted = fn.split('/')[1:] # remove DATA and PURELIB dirs
                if fn_splitted[0] == 'DLLs':
                    fn_path = os.path.join(home_dir, *fn_splitted)
                elif fn_splitted[0].endswith('.egg-info'):
                    if fn_splitted[1] == 'PKG-INFO':
                        fn_path = os.path.join(lib_dir, 'site-packages', fn_splitted[0])
                    else:
                        continue
                else:
                    fn_path = os.path.join(lib_dir, 'site-packages', *fn_splitted)
                if not os.path.exists(os.path.dirname(fn_path)):
                    os.makedirs(os.path.dirname(fn_path))
                f = open(fn_path, 'wb')
                f.write(zip.read(fn))
                f.close()
            print >> sys.stdout, 'Installed ' \\
                     + os.path.abspath(os.path.join(lib_dir,
                                                    'site-packages',
                                                    'shapely'))
        except urllib2.HTTPError:
            # handle exception
            print >> sys.stderr, 'Error when downloading. Abort...'
"""

def generate(filename, version):
    # what's commented out below comes from go-pylons.py

    #path = version
    #if '==' in version:
    #    path = version[:version.find('==')]
    #output = virtualenv.create_bootstrap_script(
    #    textwrap.dedent(after_install % (path, version)))

    output = virtualenv.create_bootstrap_script(
        textwrap.dedent(after_install % (version, version)))
    fp = open(filename, 'w')
    fp.write(output)
    fp.close()


def main():
    if len(sys.argv) > 2:
        print >> sys.stderr, 'Usage: %s [version]' % sys.argv[0]
        sys.exit(1)
    
    if len(sys.argv) == 2:
        version = sys.argv[1]
        print >> sys.stdout, 'Generating go script for installation of ' \
                'version %s of MapFish' % version
    else:
        version = 'all'
        print >> sys.stdout, 'Version has not been specified:'
        print >> sys.stdout, 'Generating go script for installation of ' \
                'development version of MapFish'

    filename = 'go-mapfish-framework-%s.py' % version
    generate(filename, version)


if __name__ == '__main__':
    main()

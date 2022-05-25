#!/usr/bin/env python

from setuptools import setup, Extension
from distutils.command.install_headers import install_headers
import os, sys, platform
from glob import glob

class Dummy:
    pass
pkginfo = Dummy()
execfile('Scientific/__pkginfo__.py', pkginfo.__dict__)

# Check for Cython and use it if the environment variable
# COMPILE_CYTHON is set to a non-zero value.
use_cython = int(os.environ.get('COMPILE_CYTHON', '0')) != 0
if use_cython:
    try:
        from Cython.Build import cythonize
        use_cython = True
    except ImportError:
        use_cython = False

src_ext = 'pyx' if use_cython else 'c'

cmdclass = {}
extra_compile_args = ["-DNUMPY=1"]
numpy_include = []
data_files = []
scripts = []
options = {}

import numpy.distutils.misc_util
numpy_include = numpy.distutils.misc_util.get_numpy_include_dirs()

math_libraries = []
if sys.platform != 'win32':
    math_libraries.append('m')

#
# Locate netCDF library
#
netcdf_prefix = None
for arg in sys.argv[1:]:
    if arg[:16] == "--netcdf_prefix=":
        netcdf_prefix = arg[16:]
        sys.argv.remove(arg)
        break

if sys.platform == 'win32':
    netcdf_dll = None
    for arg in sys.argv[1:]:
        if arg[:13] == "--netcdf_dll=":
            netcdf_dll = arg[13:]
            sys.argv.remove(arg)
            break

if netcdf_prefix is None:
    try:
        netcdf_prefix=os.environ['NETCDF_PREFIX']
    except KeyError:
        pass
if netcdf_prefix is None:
    for netcdf_prefix in ['/usr/local', '/usr', '/sw']:
        netcdf_include = os.path.join(netcdf_prefix, 'include')
        netcdf_lib = os.path.join(netcdf_prefix, 'lib')
        if os.path.exists(os.path.join(netcdf_include, 'netcdf.h')):
            break
    else:
        netcdf_prefix = None

if netcdf_prefix is None:
    print "netCDF not found, the netCDF module will not be built!"
    if sys.platform != 'win32':
        print "If netCDF is installed somewhere on this computer,"
        print "please set NETCDF_PREFIX to the path where"
        print "include/netcdf.h and lib/netcdf.a are located"
        print "and re-run the build procedure."
    ext_modules = []
else:
    if sys.platform == 'win32':
        if netcdf_dll is None:
            print "Option --netcdf_dll is missing"
            raise SystemExit
        netcdf_include = netcdf_prefix
        netcdf_h_file = os.path.join(netcdf_prefix, 'netcdf.h')
        netcdf_lib = netcdf_dll
        data_files.append(('DLLs', [os.path.join(netcdf_dll, 'netcdf.dll')]))
        scripts.append('scientific_win32_postinstall.py')
        options['bdist_wininst'] = {'install_script': "scientific_win32_postinstall.py"}
    else:
        print "Using netCDF installation in ", netcdf_prefix
        netcdf_include = os.path.join(netcdf_prefix, 'include')
        netcdf_h_file = os.path.join(netcdf_prefix, 'include', 'netcdf.h')
        netcdf_lib = os.path.join(netcdf_prefix, 'lib')
    ext_modules = [Extension('Scientific._netcdf',
                             ['Scientific/_netcdf.c'],
                             include_dirs=['Include', netcdf_include]
                                          + numpy_include,
                             library_dirs=[netcdf_lib],
                             libraries = ['netcdf'],
                             extra_compile_args=extra_compile_args)]

try:
    # Add code for including documentation in Mac packages
    import bdist_mpkg
    from distutils.command.bdist_mpkg import bdist_mpkg as bdist_mpkg
    class my_bdist_mpkg(bdist_mpkg):
        def initialize_options(self):
            bdist_mpkg.initialize_options(self)

            self.scheme_descriptions['examples'] = u'(Optional) ScientificPython example code'
            self.scheme_map['examples'] = '/Developer/Python/ScientificPython/Examples'
            self.scheme_copy['examples'] = 'Examples'

            self.scheme_descriptions['doc'] = u'(Optional) ScientificPython documentation'
            self.scheme_map['doc'] = '/Developer/Python/ScientificPython/Documentation'
            self.scheme_copy['doc'] = 'Doc'

    cmdclass['bdist_mpkg'] = my_bdist_mpkg

except ImportError:
    pass

packages = ['Scientific', 'Scientific.Clustering', 'Scientific.Functions',
            'Scientific.Geometry', 'Scientific.IO',
            'Scientific.Physics', 'Scientific.QtWidgets',
            'Scientific.Statistics', 'Scientific.Signals',
            'Scientific.Threading', 'Scientific.TkWidgets',
            'Scientific.Visualization', 'Scientific.MPI',
            'Scientific.DistributedComputing']

ext_modules.append(Extension('Scientific._vector',
                             ['Scientific/_vector.%s' % src_ext],
                             include_dirs=['Include']+numpy_include,
                             libraries=math_libraries,
                             extra_compile_args=extra_compile_args))
ext_modules.append(Extension('Scientific._affinitypropagation',
                             ['Scientific/_affinitypropagation.%s' % src_ext],
                             include_dirs=['Include']+numpy_include,
                             libraries=math_libraries,
                             extra_compile_args=extra_compile_args))
ext_modules.append(Extension('Scientific._interpolation',
                             ['Scientific/_interpolation.%s' % src_ext],
                             include_dirs=['Include']+numpy_include,
                             libraries=math_libraries,
                             extra_compile_args=extra_compile_args))

if use_cython:
    ext_modules = cythonize(ext_modules)

scripts.append('task_manager')
if sys.version[:3] >= '2.1':
    packages.append('Scientific.BSP')
    scripts.append('bsp_virtual')

class modified_install_headers(install_headers):

    def finalize_options(self):
        install_headers.finalize_options(self)
        self.install_dir = \
                os.path.join(os.path.split(self.install_dir)[0], 'Scientific')

cmdclass['install_headers'] = modified_install_headers

headers = glob(os.path.join ("Include","Scientific","*.h"))
if netcdf_prefix is not None:
    headers.append(netcdf_h_file)

setup (name = "ScientificPython",
       version = pkginfo.__version__,
       description = "Various Python modules for scientific computing",
       long_description = 
"""ScientificPython is a collection of Python modules that are useful
for scientific computing. In this collection you will find modules
that cover basic geometry (vectors, tensors, transformations, vector
and tensor fields), quaternions, automatic derivatives, (linear)
interpolation, polynomials, elementary statistics, nonlinear
least-squares fits, unit calculations, Fortran-compatible text
formatting, 3D visualization via VRML, and two Tk widgets for simple
line plots and 3D wireframe models.""",
       author = "Konrad Hinsen",
       author_email = "hinsen@cnrs-orleans.fr",
       url = "http://dirac.cnrs-orleans.fr/ScientificPython/",
       license = "CeCILL-C",

       packages = packages,
       headers = headers,
       ext_modules = ext_modules,
       scripts = scripts,
       data_files = data_files,
 
       cmdclass = cmdclass,
       options = options,
       )

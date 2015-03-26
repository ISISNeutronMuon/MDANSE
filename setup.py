import fnmatch
import glob
import os
import sys

import numpy

from Cython.Distutils import build_ext

from distutils.core import setup, Extension
from distutils.command.build import build
from distutils.command.build_py import build_py
from distutils.command.build_scripts import build_scripts 
from distutils.sysconfig import get_config_vars
from distutils.util import convert_path

#################################
# Modules variables
#################################
EXCLUDE = ['*.py', '*.pyc', '*$py.class', '*~', '.*', '*.bak', '*.so', '*.pyd']

EXCLUDE_DIRECTORIES = ('.*', 'CVS', '_darcs', './build','*svn','./dist', 'EGG-INFO', '*.egg-info')

EXTENSIONS_PATH = "Extensions"

INCLUDE_DIR = [numpy.get_include()]

QHULL_DIR = os.path.join("Extensions","qhull_lib")

QHULL_INCLUDE_DIR = INCLUDE_DIR + [EXTENSIONS_PATH] + [os.path.join(QHULL_DIR,"ext")] + [os.path.join(QHULL_DIR,"src")]

SCRIPTS_PATH = "Scripts"

#################################
# Helper function
#################################

def is_package(path):
    return (os.path.isdir(path) and os.path.isfile(os.path.join(path, '__init__.py')))

def find_packages(path, base="", exclude=None):

    packages = {}

    for item in os.listdir(path):
        d = os.path.join(path, item)
        if exclude is not None and (os.path.abspath(d) == os.path.abspath(exclude)):
            continue
        if is_package(d):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = d
            packages.update(find_packages(d, module_name, exclude))
            
    return packages

def find_package_data(where='.', package='', exclude=EXCLUDE, exclude_directories=EXCLUDE_DIRECTORIES, only_in_packages=True, show_ignored=False):
    
    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatch.fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, ("Directory %s ignored by pattern %s" % (fn, pattern))
                        break
                if bad_name:
                    continue
                if (os.path.isfile(os.path.join(fn, '__init__.py')) and not prefix):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append((fn, prefix + name + '/', package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatch.fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, ("File %s ignored by pattern %s" % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    
    return out


def find_data(where=".", exclude=EXCLUDE, exclude_directories=EXCLUDE_DIRECTORIES, prefix=""):

    out = {}
    stack = [convert_path(where)]
    while stack:
        where = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            d = os.path.join(prefix,os.path.dirname(fn))
            if os.path.isdir(fn):
                stack.append(fn)
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatch.fnmatchcase(name, pattern) or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(d, []).append(fn)
            
    out = [(k,v) for k, v in out.items()]
    
    return out


#################################
# Packages section
#################################

PACKAGE_INFO = {}
execfile('nMOLDYN/__pkginfo__.py', PACKAGE_INFO)

PACKAGES = find_packages(path=".", exclude=os.path.join("nMOLDYN","GUI"))
PACKAGES = PACKAGES.keys()

#################################
# Package data section
#################################

# Retrieve all the data related to the nMoldyn package.
PACKAGE_DATA = find_package_data(where='nMOLDYN',
                                 package='nMOLDYN',
                                 show_ignored=False)

#################################
# User data section
#################################

DATA_FILES = []

#################################
# Scripts section
#################################

SCRIPTS = []
SCRIPTS.append(os.path.join(SCRIPTS_PATH,'nmoldyn_console'))

#################################
# Extensions section
#################################

if 'linux' in sys.platform:
    (opt,) = get_config_vars('OPT')
    os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

EXTENSIONS = [Extension('nMOLDYN.Extensions.distance_histogram',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'distance_histogram.pyx')]),
              Extension('nMOLDYN.Extensions.fast_calculation',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'fast_calculation.pyx')]),
              Extension('nMOLDYN.Extensions.sas_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'sas_fast_calc.pyx')]),
              Extension('nMOLDYN.Extensions.mt_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'mt_fast_calc.pyx')]),
              Extension('nMOLDYN.Extensions.sd_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'sd_fast_calc.pyx')]),
              Extension('nMOLDYN.Extensions.mic_fast_calc', 
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'mic_fast_calc.pyx')],
                        language="c++"),
              Extension('nMOLDYN.Extensions.qhull',
                        include_dirs  = QHULL_INCLUDE_DIR,
                        sources =  glob.glob(os.path.join(QHULL_DIR, 'src','*.c')) + [os.path.join("Extensions",'qhull.pyx')],
                        define_macros = [('qh_QHpointer','1')])
              ]

class ModifiedBuildScripts(build_scripts):
    
    def finalize_options (self):

        build_scripts.finalize_options(self)

        if self.distribution.command_obj['build'].gui:
            self.scripts.append(os.path.join(SCRIPTS_PATH,'nmoldyn_gui'))
                    

class ModifiedBuildPy(build_py):

    def finalize_options(self):

        build_py.finalize_options(self)

        if self.distribution.command_obj['build'].gui:
            self.packages.append('nMOLDYN.GUI')
            self.packages.extend(find_packages(path=os.path.join("nMOLDYN","GUI"), base="nMOLDYN.GUI").keys())
             
        self.data_files = self.get_data_files()


class ModifiedBuild(build):
    
    user_options = build.user_options + [('gui',None,'Build nMOLDYN with GUI [default]'),
                                         ('no-gui', None, "Build nMOLDYN without GUI")]
    
    boolean_options = build.boolean_options + ['gui']

    negative_opt = {'no-gui' : 'gui'}

    def initialize_options(self):
        build.initialize_options(self)
        self.gui = 1
 
         
#################################
# The setup section
#################################

setup (name             = "nMOLDYN",
       version          = PACKAGE_INFO["__version__"],
       description      = "Analysis of Molecular Dynamics trajectories",
       long_description =
"""nMOLDYN is an interactive program for the analysis of Molecular
Dynamics simulations. It is especially designed for the computation
and decomposition of neutron scattering spectra. The structure and
dynamics of the simulated systems can be characterized in terms of
various space and time correlation functions. To analyze the dynamics
of complex systems, rigid-body motions of arbitrarily chosen molecular
subunits can be studied.
""",
       author           = "B. Aoun & G. Goret & E. Pellegrini, G.R. Kneller",
       author_email     = "aoun.ill.fr, goretg@ill.fr, pellegrini@ill.fr, kneller@cnrs-orleans.fr",
       maintainer       = "B. Aoun, G. Goret, E. Pellegrini",
       maintainer_email = "aoun.ill.fr, goretg.ill.fr, pellegrini@ill.fr",
       url              = "https://forge.epn-campus.eu/projects/nmoldyn/",
       license          = "CeCILL",
       packages         = PACKAGES,
       package_data     = PACKAGE_DATA,
       data_files       = DATA_FILES,
       platforms        = ['Unix','Windows'],
       ext_modules      = EXTENSIONS,
       scripts          = SCRIPTS,
        cmdclass         = {'build_ext'     : build_ext,
                            'build'         : ModifiedBuild,
                            'build_py'      : ModifiedBuildPy,
                            'build_scripts' : ModifiedBuildScripts}
       )

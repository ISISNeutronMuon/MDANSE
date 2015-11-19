import fnmatch
import glob
import os
import sys

import numpy

from Cython.Distutils import build_ext as cython_build_ext

from distutils.command.build import build
from distutils.core import setup, Extension
from distutils.sysconfig import get_config_vars
from distutils.util import convert_path

try:
    import sphinx
except ImportError:
    sphinx = None

try:
    import stdeb
except ImportError:
    stdeb = None

#################################
# Modules variables
#################################
EXCLUDE = ['*.py', '*.pyc', '*$py.class', '*~', '.*', '*.bak', '*.so', '*.pyd']

EXCLUDE_DIRECTORIES = ('.*', 'CVS', '_darcs', './build','*svn','./dist', 'EGG-INFO', '*.egg-info')

EXTENSIONS_PATH = "Extensions"

INCLUDE_DIR = [numpy.get_include()]

QHULL_DIR = os.path.join("Extensions","qhull_lib")

QHULL_INCLUDE_DIR = INCLUDE_DIR + [EXTENSIONS_PATH] + [os.path.join(QHULL_DIR,"ext")] + [os.path.join(QHULL_DIR,"src")]

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
execfile('MDANSE/__pkginfo__.py', PACKAGE_INFO)

PACKAGES = find_packages(path=".")
PACKAGES = PACKAGES.keys()

#################################
# Package data section
#################################

# Retrieve all the data related to the MDANSE package.
PACKAGE_DATA = find_package_data(where='MDANSE', package='MDANSE', show_ignored=False)

#################################
# User data section
#################################

DATA_FILES = []
DATA_FILES.extend(find_data('Doc',exclude=[],prefix='conf_'))

#################################
# Scripts section
#################################

SCRIPTS_PATH = "Scripts"
SCRIPTS = glob.glob(os.path.join(SCRIPTS_PATH,'mdanse*'))

#################################
# Documentation
#################################

if sphinx:
    import sphinx.apidoc
    import sphinx.setup_command

    class mdanse_build_doc(sphinx.setup_command.BuildDoc):
                              
        def run(self):
            
            build = self.get_finalized_command('build')
                    
            buildDir = os.path.abspath(build.build_lib)

            sys.path.insert(0,buildDir)

            sphinxDir = os.path.join(build.build_base,'sphinx',self.doctype)
                                 
            metadata = self.distribution.metadata
     
            sphinx.apidoc.main(['',
                                '-F',
                                '--separate',
                                '-H', metadata.name,
                                '-A', metadata.author,
                                '-V', metadata.version,
                                '-R', metadata.version,
                                '-o', sphinxDir,
                                os.path.join(buildDir,'MDANSE'),
                                os.path.join(buildDir,'MDANSE','Externals')])
                 
            curDir = os.getcwd()
                 
            import shutil
            shutil.copy(os.path.join(curDir,'Doc','conf_%s.py' % self.doctype),os.path.join(sphinxDir,'conf.py'))
            shutil.copy(os.path.join(curDir,'Doc','mdanse_logo.png'),os.path.join(sphinxDir,'_static'))
            shutil.copy(os.path.join(curDir,'Doc','layout.html'),os.path.join(sphinxDir,'_templates'))
     
            # The directory where the rst files are located.
            self.source_dir = sphinxDir
            # The directory where the conf.py file is located.
            self.config_dir = self.source_dir
     
            # The directory where the documentation will be built
            self.build_dir = os.path.join(buildDir,'MDANSE','Doc',self.doctype)
            
            self.finalize_options()
                                                     
            sphinx.setup_command.BuildDoc.run(self)
                 
            sys.path.pop(0)
            
    class mdanse_build_help(mdanse_build_doc):
        
        doctype = 'help'

    class mdanse_build_api(mdanse_build_doc):
        
        doctype = 'api'

#################################
# Debian packaging
#################################

class mdanse_build(build):

    def has_sphinx(self):
        if sphinx is None:
            return False
        setup_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.isdir(os.path.join(setup_dir, 'Doc'))
    
    sub_commands = build.sub_commands + [('build_api', has_sphinx),('build_help',has_sphinx)]
                        
#################################
# Extensions section
#################################

if 'linux' in sys.platform:
    (opt,) = get_config_vars('OPT')
    os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

EXTENSIONS = [Extension('MDANSE.Extensions.distance_histogram',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'distance_histogram.pyx')]),
              Extension('MDANSE.Extensions.fast_calculation',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'fast_calculation.pyx')]),
              Extension('MDANSE.Extensions.sas_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'sas_fast_calc.pyx')]),
              Extension('MDANSE.Extensions.mt_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'mt_fast_calc.pyx')]),
              Extension('MDANSE.Extensions.sd_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'sd_fast_calc.pyx')]),
              Extension('MDANSE.Extensions.mic_fast_calc', 
                        include_dirs=INCLUDE_DIR,
                        sources = [os.path.join("Extensions",'mic_fast_calc.pyx')],
                        language="c++"),
              Extension('MDANSE.Extensions.qhull',
                        include_dirs  = QHULL_INCLUDE_DIR,
                        sources =  glob.glob(os.path.join(QHULL_DIR, 'src','*.c')) + [os.path.join("Extensions",'qhull.pyx')],
                        define_macros = [('qh_QHpointer','1')])
              ]

CMDCLASS = {'build'     : mdanse_build,
            'build_ext' : cython_build_ext}

if sphinx:
    CMDCLASS['build_api'] = mdanse_build_api
    CMDCLASS['build_help'] = mdanse_build_help
             
#################################
# The setup section
#################################

setup (name             = "MDANSE",
       version          = PACKAGE_INFO["__version__"],
       description      = "Analysis of Molecular Dynamics trajectories",
       long_description =
"""MDANSE is an interactive program for the analysis of Molecular
Dynamics simulations. It is especially designed for the computation
and decomposition of neutron scattering spectra. The structure and
dynamics of the simulated systems can be characterized in terms of
various space and time correlation functions. To analyze the dynamics
of complex systems, rigid-body motions of arbitrarily chosen molecular
subunits can be studied.
""",
       author           = "B. Aoun & G. Goret & E. Pellegrini",
       author_email     = "aoun.ill.fr, goretg@ill.fr, pellegrini@ill.fr",
       maintainer       = "B. Aoun, G. Goret, E. Pellegrini",
       maintainer_email = "aoun.ill.fr, goretg.ill.fr, pellegrini@ill.fr",
       url              = "https://github.com/eurydyce/MDANSE/tree/master/MDANSE",
       license          = "CeCILL",
       packages         = PACKAGES,
       package_data     = PACKAGE_DATA,
       data_files       = DATA_FILES,
       platforms        = ['Unix','Windows'],
       ext_modules      = EXTENSIONS,
       scripts          = SCRIPTS,
       cmdclass         = CMDCLASS,
       install_requires = ['Jinja2'])

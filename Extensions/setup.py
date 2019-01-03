import glob
import os
import sys

from Cython.Distutils import build_ext

from distutils.core import setup, Extension
from distutils.sysconfig import get_config_vars

import numpy

if 'linux' in sys.platform:
    (opt,) = get_config_vars('OPT')
    os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

INCLUDE_DIR = [numpy.get_include()]

QHULL_DIR = os.path.join("qhull_lib")

QHULL_INCLUDE_DIR = INCLUDE_DIR + [os.path.join(QHULL_DIR,"ext")] + [os.path.join(QHULL_DIR,"src")]

EXTENSIONS = [Extension('distance_histogram',
                        include_dirs=INCLUDE_DIR,
                        sources = ['distance_histogram.pyx']),
              Extension('fast_calculation',
                        include_dirs=INCLUDE_DIR,
                        sources = ['fast_calculation.pyx']),
              Extension('sas_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = ['sas_fast_calc.pyx']),
              Extension('mt_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = ['mt_fast_calc.pyx']),
              Extension('sd_fast_calc',
                        include_dirs=INCLUDE_DIR,
                        sources = ['sd_fast_calc.pyx']),
              Extension('mic_fast_calc', 
                        include_dirs=INCLUDE_DIR,
                        sources = ['mic_fast_calc.pyx'],
                        language="c++"),
              Extension('qhull',
                        include_dirs  = QHULL_INCLUDE_DIR,
                        sources =  glob.glob(os.path.join(QHULL_DIR, 'src','*.c')) + ['qhull.pyx'],
                        define_macros = [('qh_QHpointer','1')]),
              Extension('mdanse_xtc',
                        include_dirs=[numpy.get_include(),'./xtc/include/','./xtc/'],
                        sources=['./xtc/src/xdrfile.c',
                                 './xtc/src/xdr_seek.c',
                                 './xtc/src/xdrfile_xtc.c',
                                 './xtc/xtc.pyx'])
              ]



setup (name = "MDANSE_Extensions",
           version = "1.0",
           ext_modules = EXTENSIONS,                 
           cmdclass = {'build_ext': build_ext})

import fnmatch
import glob
import os
import sys

import numpy

from setuptools import setup, Extension, find_packages
from Cython.Distutils import build_ext as cython_build_ext

from distutils.sysconfig import get_config_vars
from distutils.util import convert_path

try:
    import sphinx
except ImportError:
    sphinx = None


#################################
# Modules variables
#################################
EXCLUDE = ["*.py", "*.pyc", "*$py.class", "*~", ".*", "*.bak", "*.so", "*.pyd"]

EXCLUDE_DIRECTORIES = (
    ".*",
    "CVS",
    "_darcs",
    "./build",
    "*svn",
    "./dist",
    "EGG-INFO",
    "*.egg-info",
)

EXTENSIONS_PATH = "Extensions"

INCLUDE_DIR = [numpy.get_include()]

#################################
# Helper function
#################################


def is_package(path):
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "__init__.py"))


def find_package_data(
    where=".",
    package="",
    exclude=EXCLUDE,
    exclude_directories=EXCLUDE_DIRECTORIES,
    only_in_packages=True,
    show_ignored=False,
):
    out = {}
    stack = [(convert_path(where), "", package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (
                        fnmatch.fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()
                    ):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "Directory %s ignored by pattern %s" % (fn, pattern)
                            )
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, "__init__.py")) and not prefix:
                    if not package:
                        new_package = name
                    else:
                        new_package = package + "." + name
                    stack.append((fn, "", new_package, False))
                else:
                    stack.append((fn, prefix + name + "/", package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (
                        fnmatch.fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()
                    ):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "File %s ignored by pattern %s" % (fn, pattern)
                            )
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix + name)

    return out


def find_data(
    where=".", exclude=EXCLUDE, exclude_directories=EXCLUDE_DIRECTORIES, prefix=""
):
    out = {}
    stack = [convert_path(where)]
    while stack:
        where = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            d = os.path.join(prefix, os.path.dirname(fn))
            if os.path.isdir(fn):
                stack.append(fn)
            else:
                bad_name = False
                for pattern in exclude:
                    if (
                        fnmatch.fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()
                    ):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(d, []).append(fn)

    out = [(k, v) for k, v in out.items()]

    return out


#################################
# User data section
#################################

DATA_FILES = []


#################################
# Documentation
#################################

if sphinx:
    try:
        from sphinx.ext.apidoc import main as sphinx_apidoc_main
    except ImportError:
        from sphinx.apidoc import main as sphinx_apidoc_main

    #     class mdanse_build_doc(sphinx.setup_command.BuildDoc):
    class mdanse_build_doc:
        def run(self):
            build = self.get_finalized_command("build")

            buildDir = os.path.abspath(build.build_lib)

            if not os.path.exists(buildDir):
                raise IOError("build command must be performed prior building the doc")

            sys.path.insert(0, buildDir)

            sphinxDir = os.path.abspath(
                os.path.join(build.build_base, "sphinx", self.doctype)
            )

            if not os.path.exists(sphinxDir):
                os.makedirs(sphinxDir)

            metadata = self.distribution.metadata
            args = [
                "-F",
                "--separate",
                "-H%s" % metadata.name,
                "-A%s" % metadata.author,
                "-R%s" % metadata.version,
                "-o%s" % sphinxDir,
                os.path.join(buildDir, "MDANSE"),
                os.path.join(buildDir, "MDANSE", "Externals"),
            ]

            # /!\ apidoc.main is deprecated. The API has been broken in sphinx 1.7.0, see https://github.com/sphinx-doc/sphinx/issues/4615
            if int(sphinx.__version__.split(".")[1]) <= 6:
                args.insert(0, "")

            sphinx_apidoc_main(args)

            currentDirectory = os.getcwd()

            import shutil

            shutil.copy(
                os.path.join(currentDirectory, "Doc", "conf_%s.py" % self.doctype),
                os.path.join(sphinxDir, "conf.py"),
            )
            shutil.copy(
                os.path.join(currentDirectory, "Doc", "mdanse_logo.png"),
                os.path.join(sphinxDir, "_static"),
            )
            shutil.copy(
                os.path.join(currentDirectory, "Doc", "layout.html"),
                os.path.join(sphinxDir, "_templates"),
            )

            # The directory where the rst files are located.
            self.source_dir = sphinxDir
            # The directory where the conf.py file is located.
            self.config_dir = self.source_dir

            # The directory where the documentation will be built
            self.build_dir = os.path.join(buildDir, "MDANSE", "Doc", self.doctype)

            if isinstance(self.builder, str):
                builders = [self.builder]
            else:
                builders = self.builder

            for builder in builders:
                self.builder_target_dir = os.path.join(self.build_dir, builder)
                sphinx.setup_command.BuildDoc.finalize_options(self)
                sphinx.setup_command.BuildDoc.run(self)

            sys.path.pop(0)

    class mdanse_build_help(mdanse_build_doc):
        doctype = "help"

    class mdanse_build_api(mdanse_build_doc):
        doctype = "api"


#################################
# Extensions section
#################################

if "linux" in sys.platform:
    (opt,) = get_config_vars("OPT")
    os.environ["OPT"] = " ".join(
        flag for flag in opt.split() if flag != "-Wstrict-prototypes"
    )

EXTENSIONS = [
    Extension(
        "MDANSE.Extensions.atoms_in_shell",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "atoms_in_shell.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.change_coordinates",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "change_coordinates.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.atomic_trajectory",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "atomic_trajectory.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.fold_coordinates",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "fold_coordinates.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.com_trajectory",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "com_trajectory.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.contiguous_coordinates",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "contiguous_coordinates.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.distance_histogram",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "distance_histogram.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.fast_calculation",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "fast_calculation.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.sas_fast_calc",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "sas_fast_calc.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.mt_fast_calc",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "mt_fast_calc.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.sd_fast_calc",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "sd_fast_calc.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.mic_fast_calc",
        include_dirs=INCLUDE_DIR,
        sources=[os.path.join("Extensions", "mic_fast_calc.pyx")],
        language="c++",
    ),
    Extension(
        "MDANSE.Extensions.xtc",
        include_dirs=[
            numpy.get_include(),
            os.path.join("Extensions", "xtc", "include"),
        ],
        sources=glob.glob(os.path.join("Extensions", "xtc", "src", "*.c"))
        + [os.path.join("Extensions", "xtc", "xtc.pyx")],
    ),
    Extension(
        "MDANSE.Extensions.trr",
        include_dirs=[
            numpy.get_include(),
            os.path.join("Extensions", "xtc", "include"),
        ],
        sources=glob.glob(os.path.join("Extensions", "xtc", "src", "*.c"))
        + [os.path.join("Extensions", "xtc", "trr.pyx")],
    ),
]

for ext in EXTENSIONS:
    ext.cython_directives = {"language_level": "3"}

CMDCLASS = {"build_ext": cython_build_ext}

if sphinx:
    CMDCLASS["build_api"] = mdanse_build_api
    CMDCLASS["build_help"] = mdanse_build_help

#################################
# The setup section
#################################

setup(
    name="MDANSE",
    packages=find_packages("Src"),
    package_dir={"": "Src"},
    data_files=DATA_FILES,
    platforms=["Unix", "Windows"],
    ext_modules=EXTENSIONS,
    cmdclass=CMDCLASS,
)

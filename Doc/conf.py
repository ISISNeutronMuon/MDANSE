#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import datetime
import sys
from pathlib import Path

DOC_ROOT = Path(__file__).parent
sys.path.insert(0, DOC_ROOT)
sys.path.insert(0, DOC_ROOT.parent / "MDANSE/Src")

import MDANSE
from ruamel import yaml

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
yaml_eng = yaml.YAML()
CITATION = yaml_eng.load(DOC_ROOT.parent / "CITATION.cff")

author = ", ".join(f"{auth['given-names']} {auth['family-names']}" for auth in CITATION["authors"])

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
release = MDANSE.__version__
version, _ = MDANSE.__version__.rsplit(".", maxsplit=1)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.mathjax',
    "sphinx.ext.intersphinx",
]#,'rst2pdf.pdfbuilder']

imgmath_latex_preamble = r"\usepackage{mathrsfs}"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = {'.rst': 'restructuredtext'}

# The encoding of source files.
source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

numfig = True

current_year = datetime.date.today().year
# General information about the project.
project = 'MDANSE'
copyright = f'2015-{current_year}, MDANSE is developed and supported by the Institut Laue-Langevin and the ISIS Neutron and Muon Source'

napoleon_use_ivar = True
napoleon_use_param = False
napoleon_use_admonition_for_notes = True

html_logo = '_static/mdanse_logo.png'

inheritance_graph_attrs = {"size": '""'}
inheritance_graph_attrs = {"rankdir": "TB", "size": '""'}
inheritance_node_attrs = {"color": 'lightblue', "style": 'filled'}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("http://numpy.org/doc/2.2", None),
    "h5py": ("https://docs.h5py.org/en/stable/", None),
}

# The following is uncommented only in Windows CI/CD
#graphviz_dot = r'C:\Miniconda\envs\mdanse\Library\bin\graphviz\dot.exe'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

html_sidebars = {'**': ['localtoc.html','sourcelink.html', 'searchbox.html']}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'
# html_theme = "nature"
html_theme_options = {'sidebarwidth':250}#, 'nosidebar':True}

# Output file base name for HTML help builder.
htmlhelp_basename = 'MDANSE_doc'

html_context = {
    "display_github": True, # Integrate GitHub
    "github_user": "ISISNeutronMuon", # Username
    "github_repo": "MDANSE", # Repo name
    "github_version": "protos", # Version
    "conf_py_path": "/Doc/", # Path in the checkout to the docs root
}

latex_documents = [
    (master_doc, 'theory_help.tex', 'Theory background of MDANSE',
     'MDANSE developers', 'manual'),
]

def setup(app):
    app.add_css_file('custom.css')

#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os
import sys
import datetime

sys.path.insert(0, os.path.abspath('..'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# project = 'MDANSE'
# copyright = '2015-2022, Eric Pellegrini'
author = 'Eric Pellegrini'
release = '2.0.0a1'
version = '2.0'

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
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.mathjax',
]#,'rst2pdf.pdfbuilder']

imgmath_latex_preamble = "\\usepackage{mathrsfs}"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

numfig = True

current_year = datetime.date.today().year
# General information about the project.
project = u'MDANSE'
copyright = u'2015-' + str(current_year) + u', MDANSE is developed and supported by the Institut Laue-Langevin and the ISIS Neutron and Muon Source, ![UKRI Logo](_static/UKRI_Logo.png)'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.

html_logo = '_static/mdanse_logo.png'

inheritance_graph_attrs = dict(size='""')

inheritance_graph_attrs = dict(rankdir="TB", size='""')

inheritance_node_attrs = dict(color='lightblue', style='filled')

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

latex_documents = [
    (master_doc, 'theory_help.tex', 'Theory background of MDANSE',
     'MDANSE developers', 'manual'),
]

def setup(app):
    app.add_css_file('custom.css')

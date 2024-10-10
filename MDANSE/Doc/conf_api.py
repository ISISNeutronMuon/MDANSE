# MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
# ------------------------------------------------------------------------------------------
# Copyright (C)
# 2015- Eric C. Pellegrini Institut Laue-Langevin
# BP 156
# 6, rue Jules Horowitz
# 38042 Grenoble Cedex 9
# France
# pellegrini[at]ill.fr
# goret[at]ill.fr
# aoun[at]ill.fr
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

""" 
Created on Mar 30, 2015

@author: Gael Goret and Eric C. Pellegrini
"""

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "1.0"

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.pngmath",
]  # ,'rst2pdf.pdfbuilder']

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
source_encoding = "utf-8-sig"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "MDANSE"
copyright = "2015, Gael Goret, Bachir Aoun and Eric C. Pellegrini"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = "1.0"
# The full version, including alpha/beta/rc tags.
release = "1.0"

# html_logo = "_static/mdanse_logo.png"

inheritance_graph_attrs = dict(size='""')

inheritance_graph_attrs = dict(rankdir="TB", size='""')

inheritance_node_attrs = dict(color="lightblue", style="filled")

# The following is uncommented only in Windows CI/CD
# graphviz_dot = r'C:\Miniconda\envs\mdanse\Library\bin\graphviz\dot.exe'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ---------------------------------------------------

html_sidebars = {"**": ["localtoc.html", "sourcelink.html", "searchbox.html"]}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "nature"
html_theme_options = {"sidebarwidth": 250}  # , 'nosidebar':True}

# Output file base name for HTML help builder.
htmlhelp_basename = "MDANSE_doc"

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    (
        "index",
        "MDANSE.tex",
        "MDANSE Documentation",
        "Gael Goret \\& Eric C. Pellegrini",
        "manual",
    ),
]

pdf_documents = [
    ("index", "MDANSE", "MDANSE Documentation", "Gael Goret & Eric C. Pellegrini"),
]

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("index", "MDANSE", "MDANSE Documentation", "Gael Goret & Eric C. Pellegrini"),
]

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "MDANSE",
        "MDANSE Documentation",
        "Gael Goret & Eric C. Pellegrini",
        "MDANSE",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# List of directories, relative to source directory, that shouldn't be searched for source files.
exclude_patterns = ["Externals"]

members_to_watch = ["class"]

from MDANSE.Framework.Jobs.IJob import IJob

klsNames = [kls.__name__ for kls in IJob.indirect_subclasses()]


def flag_onthefly(app, what, name, obj, options, lines):
    if getattr(obj, "__name__", None) in klsNames:
        lines.extend(obj.build_doc().splitlines())

    if what in members_to_watch:
        # modify the docstring so the rendered output is highlights the omission
        if lines:
            lines.insert(0, "")
            lines.insert(0, ":Description:")
            lines.insert(0, "")
            lines.insert(0, ".. inheritance-diagram:: %s" % name.split(".")[-1])
            lines.insert(0, "")
            lines.insert(0, "**Inheritance-diagram:**")
            lines.insert(0, "")


def setup(app):
    app.connect("autodoc-process-docstring", flag_onthefly)

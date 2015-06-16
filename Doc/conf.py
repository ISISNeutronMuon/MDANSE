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

''' 
Created on Mar 30, 2015

@author: goret
'''


# import os
# import shutil
# import sys
# 
# import MDANSE

# MDANSE_PATH = os.path.abspath('../MDANSE')

# sys.path.append(os.path.dirname(__file__))

#
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.append(MDANSE_PATH)

# DOC_PATH = os.path.join(MDANSE_PATH,'Doc')
# if not os.path.exists(DOC_PATH):
#     os.makedirs(DOC_PATH)
# 
# shutil.copy('mdanse_logo.png',DOC_PATH)

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.graphviz', 'sphinx.ext.inheritance_diagram', 'sphinx.ext.pngmath']#,'rst2pdf.pdfbuilder']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'MDANSE'
copyright = u'2015, Gael Goret, Bachir Aoun and Eric C. Pellegrini'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0'

html_logo = '_static/mdanse_logo.png'

inheritance_graph_attrs = dict(size='""')

inheritance_graph_attrs = dict(rankdir="TB", size='""')

inheritance_node_attrs = dict(color='lightblue', style='filled')

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

html_sidebars = {'**': ['localtoc.html','sourcelink.html', 'searchbox.html']}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "nature"
html_theme_options = {'sidebarwidth':250}#, 'nosidebar':True}

# Output file base name for HTML help builder.
htmlhelp_basename = 'MDANSE_doc'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'MDANSE.tex', u'MDANSE Documentation',
   u'Gael Goret \\& Eric C. Pellegrini', 'manual'),
]

pdf_documents = [('index', 'MDANSE', u'MDANSE Documentation', u'Gael Goret & Eric C. Pellegrini'),]

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [('index', 'MDANSE', u'MDANSE Documentation', u'Gael Goret & Eric C. Pellegrini'),]

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [('index', 'MDANSE', u'MDANSE Documentation',u'Gael Goret & Eric C. Pellegrini','MDANSE', 'One line description of project.','Miscellaneous'),]

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_patterns = ['Externals']

members_to_watch = ['class']

def flag_onthefly(app, what, name, obj, options, lines):
	from MDANSE import REGISTRY
	for kls in REGISTRY["job"].values():
		kls.__doc__ += kls.build_doc()
	if(what in members_to_watch):
		# and modify the docstring so the rendered output is highlights the omission
		if lines:
			lines.insert(0,'**Description:**\n\n')
			lines.insert(0,'    .. inheritance-diagram:: %s\n'%name.split('.')[-1])
			lines.insert(0,'**inheritance-diagram:**\n\n')

# def setup(app):
# 
# 	app.connect('autodoc-process-docstring', flag_onthefly)
	

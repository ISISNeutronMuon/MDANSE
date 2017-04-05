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
Created on Mar 26, 2015

:author: Eric C. Pellegrini
'''

import os
import warnings
warnings.filterwarnings("ignore")

from __pkginfo__ import __version__, __author__, __date__

from MDANSE.Logging.Logger import LOGGER

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.ClassRegistry import REGISTRY

from MDANSE.Data.ElementsDatabase import ELEMENTS

import MDANSE.Framework

PLATFORM.create_directory(PLATFORM.macros_directory())

# MMTK imports.
from MMTK import Database

# The default database is still the MMTK one
Database.path.append(os.path.join(PLATFORM.package_directory(), 'Data'))
Database.path.append(os.path.join(PLATFORM.application_directory(), 'mmtk_database'))

# Update the database with user defined atom entries
import glob
userDefinedAtoms =  glob.glob(os.path.join(PLATFORM.application_directory(), 'mmtk_database','Atoms','*'))
for atomFile in userDefinedAtoms:
    atomName = os.path.basename(atomFile)
    if not ELEMENTS.has_element(atomName):
        ELEMENTS.add_element(atomName)
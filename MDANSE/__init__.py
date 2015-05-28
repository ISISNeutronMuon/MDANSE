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

@author: Eric C. Pellegrini
'''

from __pkginfo__ import __version__, __author__, __date__

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.ClassRegistry import ClassRegistry as REGISTRY

from MDANSE.Data.ElementsDatabase import ELEMENTS

from MDANSE.Logging.Logger import LOGGER

from MDANSE.Core.Preferences import PREFERENCES

from MDANSE.Framework.UserDefinitions.IUserDefinition import UD_STORE

import os

# MMTK imports.
from MMTK import Database
from MMTK.Database import path
from MMTK.Utility import checkURL, isURL, joinURL

def databasePath(filename, directory, try_direct = False):
        
    if isURL(filename):
        return filename
    
    filename = os.path.expanduser(filename)
    
    if try_direct and os.path.exists(filename):
        return os.path.normcase(filename)
    
    entries = None
    
    dirname,basename = os.path.split(filename) 
    
    if dirname == '':
        for p in path:
            if isURL(p):
                url = joinURL(p, directory+'/'+basename)
                if checkURL(url):
                    entries = url
                    break
            else:
                full_name = os.path.join(os.path.join(p, directory), basename)
                if os.path.exists(full_name):
                    entries = os.path.normcase(full_name)
                    break

    if entries is  None:
        if directory == "Atoms":
            LOGGER("Atom %r not found in the MMTK database. nMolDyn will create a default one." % basename,"warning")
            ELEMENTS.add_element(basename,save=True)
            return os.path.join(PLATFORM.local_mmtk_database_directory(),"Atoms", basename)
        else:
            raise IOError("Database entry %s/%s not found" % (directory, filename))
    else:
        return entries

# Add the path to the nmoldyn database to complete the MMTK database.
Database.databasePath = databasePath
Database.path.insert(0,os.path.join(PLATFORM.package_directory(), 'Data'))
Database.path.insert(0,PLATFORM.local_mmtk_database_directory())

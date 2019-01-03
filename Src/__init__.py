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
Database.path = []
Database.path.append(os.path.join(PLATFORM.package_directory(), 'Data'))
Database.path.append(os.path.join(PLATFORM.application_directory(), 'mmtk_database'))

# Update the database with user defined atom entries
import glob
userDefinedAtoms =  glob.glob(os.path.join(PLATFORM.application_directory(), 'mmtk_database','Atoms','*'))
for atomFile in userDefinedAtoms:
    atomName = os.path.basename(atomFile)
    if not ELEMENTS.has_element(atomName):
        ELEMENTS.add_element(atomName)

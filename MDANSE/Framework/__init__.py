from MDANSE.Framework.Configurators import *
from MDANSE.Framework.Formats import *
from MDANSE.Framework.Handlers import *
from MDANSE.Framework.InputData import *
from MDANSE.Framework.InstrumentResolutions import *
from MDANSE.Framework.Jobs import *
from MDANSE.Framework.OutputVariables import *
from MDANSE.Framework.Projectors import *
from MDANSE.Framework.QVectors import *
from MDANSE.Framework.Selectors import *

import os

from MDANSE import PLATFORM,REGISTRY
 
macrosDirectories = sorted([x[0] for x in os.walk(PLATFORM.macros_directory())][0:])
 
for d in macrosDirectories:
    REGISTRY.update(d)

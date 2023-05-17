# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import warnings
warnings.filterwarnings("ignore")

from .__pkginfo__ import __version__, __author__, __date__

from MDANSE.Logging.Logger import LOGGER

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.ClassRegistry import REGISTRY

import MDANSE.Framework

PLATFORM.create_directory(PLATFORM.macros_directory())

import vtk
vtk.vtkObject.GlobalWarningDisplayOff()

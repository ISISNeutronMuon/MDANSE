# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/XPLOR.py
# @brief     Implements module/class/test XPLOR
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DCDConverter import DCDConverter

class XPLORConverter(DCDConverter):
    """
    Converts an Xplor trajectory to a MMTK trajectory.
    """
    
    label = "XPLOR"

REGISTRY['xplor'] = XPLORConverter

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DMol.py
# @brief     Implements module/class/test DMol
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Discover import DiscoverConverter
        
class DMolConverter(DiscoverConverter):
    """
    Converts a DMol trajectory to a MMTK trajectory.
    """
    
    label = "DMol"
    
REGISTRY['dmol'] = DMolConverter

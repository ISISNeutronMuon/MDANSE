# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Projectors/NullProjector.py
# @brief     Implements module/class/test NullProjector
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Projectors.IProjector import IProjector

class NullProjector(IProjector):

    def set_axis(self, axis):
        pass
    
    def __call__(self, value):
        
        return value

REGISTRY['null'] = NullProjector
        

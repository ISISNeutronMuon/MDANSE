# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DFTB.py
# @brief     Implements module/class/test DFTB
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from collections import OrderedDict
import os

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Forcite import ForciteConverter


class DFTBConverter(ForciteConverter):
    """
    Converts a DFTB trajectory to a MMTK trajectory.
    """
    
    label = "DFTB"

    settings = OrderedDict()
    settings['xtd_file'] = ('input_file',
                            {'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'DFTB', 'H2O.xtd')})
    settings['trj_file'] = ('input_file',
                            {'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'DFTB', 'H2O.trj')})
    settings['output_files'] = ('output_files', {'formats': ["netcdf"]})


REGISTRY['dftb'] = DFTBConverter

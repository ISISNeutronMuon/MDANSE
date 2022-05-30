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
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from collections import OrderedDict
import os

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Forcite import ForciteConverter


class DFTBConverter(ForciteConverter):
    """
    Converts a DFTB trajectory to a HDF trajectory.
    """
    
    label = "DFTB"

    settings = OrderedDict()
    settings['xtd_file'] = ('input_file',
                            {'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'DFTB', 'H2O.xtd')})
    settings['trj_file'] = ('input_file',
                            {'default': os.path.join('..', '..', '..', 'Data', 'Trajectories', 'DFTB', 'H2O.trj')})
    settings['fold'] = ('boolean', {'default':True,'label':"Fold coordinates in to box"})
    settings['output_file'] = ('single_output_file', {'format': 'netcdf', 'root': 'xtd_file'})


REGISTRY['dftb'] = DFTBConverter

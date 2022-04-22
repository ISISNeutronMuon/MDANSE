# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Converter.py
# @brief     Implements module/class/test Converter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Framework.Jobs.IJob import IJob

class Converter(IJob):

    __metaclass__ = abc.ABCMeta
    
    category = ('Converters',)
    
    ancestor = ['empty_data']

    @abc.abstractmethod
    def run_step(self,index):
        pass

    def finalize(self):

        if not hasattr(self,'_trajectory'):
            return

        try:
            f = NetCDFFile(self._trajectory.filename,'a')
        except:
            return
        
        try:
            if 'time' in f.variables:
                f.variables['time'].units = 'ps'
                f.variables['time'].axis = 'time'
                f.variables['time'].name = 'time'

            if 'box_size' in f.variables:
                f.variables['box_size'].units = 'ps'
                f.variables['box_size'].axis = 'time'
                f.variables['box_size'].name = 'box_size'

            if 'configuration' in f.variables:
                f.variables['configuration'].units = 'nm'
                f.variables['configuration'].axis = 'time'
                f.variables['configuration'].name = 'configuration'

            if 'velocities' in f.variables:
                f.variables['velocities'].units = 'nm/ps'
                f.variables['velocities'].axis = 'time'
                f.variables['velocities'].name = 'velocities'

            if 'gradients' in f.variables:
                f.variables['gradients'].units = 'amu*nm/ps'
                f.variables['gradients'].axis = 'time'
                f.variables['gradients'].name = 'gradients'
        finally:
            f.close()


# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/DispersionLatticeQVectors.py
# @brief     Implements module/class/test DispersionLatticeQVectors
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class DispersionLatticeQVectors(LatticeQVectors):
    """
    """

    settings = collections.OrderedDict()
    settings['start'] = ('vector', {"valueType":int, "notNull":False, "default":[0,0,0]})
    settings['direction'] = ('vector', {"valueType":int, "notNull":True, "default":[1,0,0]})
    settings['n_steps'] = ('integer', {"label":"number of steps", "mini":1, "default":10})

    def _generate(self):

        start = self._configuration["start"]["value"]
        direction = self._configuration["direction"]["value"]
        n_steps = self._configuration["n_steps"]["value"]

        hkls = np.array(start)[:,np.newaxis] + np.outer(direction,np.arange(0,n_steps))
        
        # The k matrix (3,n_hkls)
        vects = np.dot(self._inverseUnitCell,hkls)
                
        dists = np.sqrt(np.sum(vects**2,axis=0))

        if self._status is not None:
            self._status.start(len(dists))

        self._configuration["q_vectors"] = collections.OrderedDict()
                                
        for i,v in enumerate(dists):

            self._configuration["q_vectors"][v] = {}
            self._configuration["q_vectors"][v]['q_vectors'] = vects[:,i][:,np.newaxis]
            self._configuration["q_vectors"][v]['n_q_vectors'] = 1
            self._configuration["q_vectors"][v]['q'] = v
            self._configuration["q_vectors"][v]['hkls'] = hkls[:,i][:,np.newaxis]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()

REGISTRY["dispersion_lattice"] = DispersionLatticeQVectors

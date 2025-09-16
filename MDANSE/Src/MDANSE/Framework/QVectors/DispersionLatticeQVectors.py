#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import collections

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class DispersionLatticeQVectors(LatticeQVectors):
    r"""Generates Q vectors along a line in the HKL units of the simulation box.

    The input 'start' and 'step' vectors are expressed as HKL values of the
    crystal lattice defined by the simulation box. Every vector will be
    generated as :math:`\mathbf{k}_{start} + n\mathbf{k}_{step}` for
    integer n from 0 to n_steps.

    The 'using_supercell' input is only used for the final conversion
    of q vectors to HKL coordinates. If the simulated cell is a supercell,
    you can specify the multiplicity of the supercell here to have the
    HKL values generated in the units of the original unit cell."""

    settings = collections.OrderedDict()
    settings["start"] = (
        "VectorConfigurator",
        {"valueType": float, "notNull": False, "default": [0, 0, 0]},
    )
    settings["step"] = (
        "VectorConfigurator",
        {"valueType": float, "notNull": True, "default": [1, 0, 0]},
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {"label": "number of steps", "mini": 1, "default": 10},
    )
    settings["using_supercell"] = (
        "VectorConfigurator",
        {"valueType": int, "notNull": True, "default": [1, 1, 1]},
    )

    def _generate(self):
        start = self._configuration["start"]["value"].array
        step_vector = self._configuration["step"]["value"]
        n_steps = self._configuration["n_steps"]["value"]
        scell_multiple = self._configuration["using_supercell"]["value"]

        hkls = np.array(start)[:, np.newaxis] + np.outer(
            step_vector, np.arange(0, n_steps)
        )
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)
        q_vectors, weights = self.lattice_vectors_with_weights(vects, self._unit_cell)
        # The k matrix (3,n_hkls)

        dists = np.sqrt(np.sum(q_vectors**2, axis=0))
        keyvals = dists * np.sign(
            np.dot(step_vector, self.qvectors_to_hkl(q_vectors, self._unit_cell))
        )

        if self._status is not None:
            self._status.start(len(dists))

        self._configuration["q_vectors"] = collections.OrderedDict()

        base_cell = UnitCell(
            self._unit_cell._unit_cell / (np.array(scell_multiple)[:, None])
        )
        base_hkls = self.qvectors_to_hkl(q_vectors, base_cell)

        for i, v in enumerate(keyvals):
            self._configuration["q_vectors"][v] = {}
            self._configuration["q_vectors"][v]["q_vectors"] = q_vectors[:, i][
                :, np.newaxis
            ]
            self._configuration["q_vectors"][v]["n_q_vectors"] = weights[i]
            self._configuration["q_vectors"][v]["weights"] = weights[i : i + 1]
            self._configuration["q_vectors"][v]["q"] = v
            self._configuration["q_vectors"][v]["hkls"] = base_hkls[:, i][:, np.newaxis]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()

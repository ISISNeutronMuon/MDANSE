from math import floor

import numpy as np

from .RangeConfigurator import RangeConfigurator


class DistHistCutoffConfigurator(RangeConfigurator):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._max_value = kwargs.get("max_value", True)

    def configure(self, value):
        """Configure the distance histogram cutoff configurator.

        Parameters
        ----------
        value : tuple
            A tuple of the range parameters.
        """
        if self._max_value and value[1] > floor(self.get_largest_cutoff() * 100) / 100:
            self.error_status = (
                "The cutoff distance goes into the simulation box periodic images."
            )
            return

        super().configure(value)

    def get_largest_cutoff(self) -> float:
        """Get the largest cutoff value for the given trajectories
        unit cells.

        Returns
        -------
        float
            The maximum cutoff for the distance histogram job.
        """
        traj_config = self._configurable[self._dependencies["trajectory"]]["instance"]
        min_d = np.min(
            [uc.direct for uc in traj_config._trajectory._unit_cells], axis=0
        )
        vec_a, vec_b, vec_c = min_d
        a = np.linalg.norm(vec_a)
        b = np.linalg.norm(vec_b)
        c = np.linalg.norm(vec_c)

        i, j, k = reversed(np.argsort([a, b, c]))
        vecs = [vec_a, vec_b, vec_c]

        cross_ij = np.cross(vecs[i], vecs[j])
        proj = cross_ij * (vecs[k] @ cross_ij) / (cross_ij @ cross_ij)
        return np.linalg.norm(proj) / 2

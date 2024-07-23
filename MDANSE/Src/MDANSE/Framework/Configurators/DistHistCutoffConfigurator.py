from math import floor

import numpy as np

from .RangeConfigurator import RangeConfigurator


class DistHistCutoffConfigurator(RangeConfigurator):

    def configure(self, value):
        """Configure the distance histogram cutoff configurator.

        Parameters
        ----------
        value : tuple
            A tuple of the range parameters.
        """
        if value[1] > floor(self.get_largest_cutoff() * 100) / 100:
            self.error_status = (
                "The cutoff distance goes into the simulation box periodic images."
            )
            return

        super().configure(value)

    def get_coordinate_span(self) -> np.ndarray:
        traj_config = self._configurable[self._dependencies["trajectory"]]["instance"]
        min_span = np.array(3 * [1e11])
        for frame in range(len(traj_config._trajectory)):
            coords = traj_config._trajectory.coordinates(frame)
            span = coords.max(axis=0) - coords.min(axis=0)
            min_span = np.minimum(span, min_span)
        return min_span

    def get_largest_cutoff(self) -> float:
        """Get the largest cutoff value for the given trajectories
        unit cells.

        Returns
        -------
        float
            The maximum cutoff for the distance histogram job.
        """
        traj_config = self._configurable[self._dependencies["trajectory"]]["instance"]
        try:
            trajectory_array = np.array(
                [
                    traj_config._trajectory.unit_cell(frame)._unit_cell
                    for frame in range(len(traj_config._trajectory))
                ]
            )
        except:
            return np.linalg.norm(self.get_coordinate_span())
        else:
            if np.allclose(trajectory_array, 0.0):
                return np.linalg.norm(self.get_coordinate_span())
            else:
                min_d = np.min(trajectory_array, axis=0)
                vec_a, vec_b, vec_c = min_d
                a = np.linalg.norm(vec_a)
                b = np.linalg.norm(vec_b)
                c = np.linalg.norm(vec_c)

                i, j, k = reversed(np.argsort([a, b, c]))
                vecs = [vec_a, vec_b, vec_c]

                cross_ij = np.cross(vecs[i], vecs[j])
                proj = cross_ij * (vecs[k] @ cross_ij) / (cross_ij @ cross_ij)
                return np.linalg.norm(proj) / 2

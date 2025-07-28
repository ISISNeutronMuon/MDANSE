from __future__ import annotations

from math import floor

import numpy as np

from .RangeConfigurator import RangeConfigurator


class DistHistCutoffConfigurator(RangeConfigurator):
    """Range of interatomic distances for a histogram.

    It does not allow distances large enough to include
    the periodic image of any atom in the system.
    """

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
        if not self.update_needed(value):
            return

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
        traj_config = self.configurable[self.dependencies["trajectory"]]["instance"]
        try:
            trajectory_array = np.array(
                [
                    traj_config.unit_cell(frame)._unit_cell
                    for frame in range(len(traj_config))
                ]
            )
        except Exception:
            return np.linalg.norm(traj_config.min_span)
        else:
            if np.allclose(trajectory_array, 0.0):
                return np.linalg.norm(traj_config.min_span)
            else:
                # calculated the radius of the largest sphere that can
                # fit into the unit cell
                min_d = np.min(trajectory_array, axis=0)
                vec_a, vec_b, vec_c = min_d

                cross_bc = np.cross(vec_b, vec_c)
                cross_ca = np.cross(vec_c, vec_a)
                cross_ab = np.cross(vec_a, vec_b)

                if (
                    np.allclose(cross_bc, 0.0)
                    or np.allclose(cross_ca, 0.0)
                    or np.allclose(cross_ab, 0.0)
                ):
                    raise ValueError("Trajectory contains invalid unit cell.")

                h_1 = abs(np.dot(vec_a, cross_bc)) / np.linalg.norm(cross_bc)
                h_2 = abs(np.dot(vec_b, cross_ca)) / np.linalg.norm(cross_ca)
                h_3 = abs(np.dot(vec_c, cross_ab)) / np.linalg.norm(cross_ab)

                return 0.5 * min(h_1, h_2, h_3)

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

import bisect
from pathlib import Path

import h5py
import numpy as np

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory

TIME_STEP_TOL = 1e-8
DATASET_CACHE_SIZE = 2**24

HDF5_DRIVERS = h5py.registered_drivers()
PRIMES = [
    10831,
    15991,
    23599,
    34871,
    51511,
    76099,
    112429,
    166099,
    245383,
    362521,
    535571,
    791251,
    1168957,
    1726993,
    2551421,
    3769397,
    5568817,
    8227259,
    12154757,
    17957167,
    26529487,
    39194117,
    57904453,
    85546733,
    126384823,
    186718139,
    275853173,
    407539309,
    602089451,
    889513501,
    1314147377,
    1941491989,
    2868316837,
    4237587173,
    6260516599,
    9249147301,
    13664483509,
    20187602569,
    29824712917,
    44062364303,
    65096752333,
    96172487161,
    142083083267,
    209910372047,
    310116892681,
    458159766907,
    676875000961,
    1000000000039,
]


def next_prime(nchunks: int) -> int:
    """Return one of the precalculated prime numbers for HDF5 chunk list.

    If the input number is larger than the largest prime from the list,
    returns the input number, which is not a prime, but can still be
    used by HDF5.

    Parameters
    ----------
    nchunks : int
        number of chunks that need to be cached.

    Returns
    -------
    int
        A prime number larger than the input number.
    """
    ip = bisect.bisect_right(PRIMES, nchunks)
    return nchunks if ip == len(PRIMES) else PRIMES[ip]


def guess_hdf5_trajectory_parameters(
    fname: str | Path,
) -> tuple[int, int] | tuple[None, None]:
    trajectory_instance = Trajectory(fname, fast_load=True)
    traj_length = len(trajectory_instance)
    chunk_size = trajectory_instance.chunk_size()
    bytes_per_num = trajectory_instance.bytes_per_num()
    if chunk_size < 0 or bytes_per_num < 0:
        return None, None
    cache_size = 200 * traj_length * chunk_size * 3 * bytes_per_num
    cache_slots = next_prime(80 * traj_length * 3)
    trajectory_instance.close()
    return cache_size, cache_slots


@IConfigurator.register("HDFTrajectoryConfigurator")
class HDFTrajectoryConfigurator(InputFileConfigurator):
    """Chooses the trajectory to be analysed.

    You can use it both with an .mdt file created by an MDANSE converter,
    or with an H5MD file if it contains complete information about the
    atom positions, time axis, physical units and atom types.
    """

    _default = "INPUT_FILENAME.mdt"
    label = "Input trajectory file"

    def configure_from_instance(self):
        if self._instance is None:
            raise RuntimeError(
                "Running configure_from_instance with no instance defined."
            )
        traj_instance = self._instance
        value = traj_instance._filename

        if value == self._original_input:
            return
        self._original_input = value

        InputFileConfigurator.configure(self, value)

        self.extract_information(traj_instance)

    def configure(self, value):
        if value == self._original_input:
            return
        self._original_input = value
        self.error_status = "OK"
        self.warning_status = ""

        match value:
            case str() | Path():
                file_name = value
                driver = None
                rdcc_nbytes, rdcc_nslots = guess_hdf5_trajectory_parameters(value)
                rdcc_w0 = None
            case (str() | Path(), str(), int(), int(), float()):
                file_name, driver, rdcc_nbytes, rdcc_nslots, rdcc_w0 = value
                driver = driver if driver in HDF5_DRIVERS else None
            case _:
                self.error_status = f"Invalid value {value!r}"
                return

        self["driver"] = driver
        self["rdcc_nbytes"] = rdcc_nbytes
        self["rdcc_nslots"] = rdcc_nslots
        self["rdcc_w0"] = rdcc_w0
        self["reopen_trajectory"] = True
        InputFileConfigurator.configure(self, file_name)
        self._original_input = value
        if "instance" in self and isinstance(self["instance"], Trajectory):
            trajectory_instance = self["instance"]
        else:
            try:
                trajectory_instance = Trajectory(
                    self["value"],
                    hdf5_driver=driver,
                    rdcc_nbytes=rdcc_nbytes,
                    rdcc_nslots=rdcc_nslots,
                    rdcc_w0=rdcc_w0,
                )
            except KeyError:
                self.error_status = f"Could not use {value} as input trajectory."
                return
        self.extract_information(trajectory_instance)
        if not trajectory_instance.non_dummy_elements:
            self.warning_status += (
                "This trajectory contains only dummy atoms. "
                "Analysis runs will fail or produce meaningless results."
            )

    def extract_information(self, trajectory_instance: Trajectory):
        self["instance"] = trajectory_instance

        self["filename"] = PLATFORM.get_path(trajectory_instance.filename)

        self["basename"] = self["filename"].name

        self["length"] = len(self["instance"])

        time_axis = self["instance"].time()
        if len(time_axis) == 0:
            self.error_status = "The trajectory does not contain any time steps"
            return
        if len(time_axis) == 1:
            self["md_time_step"] = 1.0
        else:
            time_steps = np.diff(time_axis)
            self["md_time_step"] = np.mean(time_steps)
            if not np.std(time_steps) < TIME_STEP_TOL:
                self.warning_status += (
                    f"Time step size changes between {np.min(time_steps)} and {np.max(time_steps)}."
                    " Most analysis types will not work correctly unless the time step is constant."
                )

        try:
            self["md_time_step"] = time_axis[1] - time_axis[0]
        except IndexError:
            self["md_time_step"] = 1.0
        except ValueError:
            self["md_time_step"] = 1.0

        self["time_axis"] = time_axis

        self["has_velocities"] = "velocities" in self["instance"].variables()

        self.warning_status += trajectory_instance.unit_cell_warning()

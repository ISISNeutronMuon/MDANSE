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
import datetime
import importlib
from pathlib import Path
from typing import NamedTuple

import h5py
import numpy as np
import numpy.typing as npt

from MDANSE import PLATFORM
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class SystemParameters(NamedTuple):
    traj_file: str
    system_name: str
    density: float = 1.0
    abs_xs: float = 0.0
    coh_xs: float = 1.0
    inc_xs: float = 1.0
    molar_mass: float = 10.0


class ResultParameters(NamedTuple):
    data_file: str
    signal_min: float
    signal_max: float
    signal_mean: float
    signal_sum: float
    n_q: int
    n_E: int
    q_min: float
    q_max: float
    E_min: float
    E_max: float
    coh_or_inc: str


def symmetrise_array(input_array: npt.NDArray[float]) -> npt.NDArray[float]:
    total_len = len(input_array)
    half_len = total_len // 2 + 1 if total_len % 2 else total_len // 2
    return (input_array[half_len:0:-1] + input_array[-half_len:]) / 2


def create_header(par: SystemParameters, arr: ResultParameters):
    return f"""# Format: Sqw data file for Isotropic_Sqw <http://www.mcstas.org>
# {par.system_name}
# Reference: INSERT PUBLICATION DETAILS HERE
#
# title: {par.system_name}: S(q,w) {arr.coh_or_inc} part
# Date: {datetime.datetime.today()}
# Source: {par.traj_file}
# filename: {arr.data_file}
# format: Sqw data file for Isotropic_Sqw (McStas)
# signal: Min={arr.signal_min}; Max={arr.signal_max}; Mean={arr.signal_mean}; sum={arr.signal_sum};
# type: array_2d({arr.n_q},{arr.n_E})
# xylimits: {arr.q_min} {arr.q_max} {arr.E_min} {arr.E_max}
# xlabel: Wavevector [Angs-1]
# ylabel: Energy [meV]
#
# Physical parameters:
# Comment       MDANSE calculation of the {par.coh_or_inc} part of S(q,w)
# Instrument    MDANSE {importlib.metadata.version("MDANSE")}
# Material      {par.system_name}
# Phase         TBC
# Scattering    {arr.coh_or_inc} process
# classical     1        [0=from measurement, with Bose factor included, 1=from MD, symmetric]
# density       {par.density}      [g/cm3] Material density
# sigma_abs     {par.abs_xs}   [barn] Absorption neutron cross section
# sigma_coh     {par.coh_xs}     [barn] Coherent scattering neutron cross section
# sigma_inc     {par.inc_xs}      [barn] Incoherent scattering neutron cross section
# weight        {par.molar_mass}       [g/mol] Material weight
"""


def get_trajectory_info(traj: Trajectory) -> SystemParameters:
    result = SystemParameters(
        traj_file=traj.filename, system_name=traj.chemical_system.name
    )
    return result


def get_result_info(
    data_file: h5py.File,
    data_key: str | None = None,
    q_axis_key: str | None = None,
    omega_axis_key: str | None = None,
) -> tuple[
    ResultParameters, tuple[npt.NDArray[float], npt.NDArray[float], npt.NDArray[float]]
]:
    task_name = data_file["metadata/task_name"]
    backup_keys = ("s(q,f)_total", "dcsf/s(q,f)/total", "disf/s(q,f)/total")
    axes = {
        "s(q,f)_total": ("q", "omega"),
        "dcsf/s(q,f)/total": ("dcsf/axes/q", "dcsf/axes/omega"),
        "guess": ("q", "omega"),
    }
    if data_key:
        data_array = data_file[data_key][:]
        q_array = (
            data_file[q_axis_key][:] if q_axis_key else data_file[axes["guess"][0]][:]
        )
        if omega_axis_key:
            omega_array = data_file[omega_axis_key][:]
        else:
            omega_array = data_file[axes["guess"][1]][:]
    else:
        for key in backup_keys:
            if key in data_file:
                data_key = key
                data_array = data_file[key][:]
                break
        q_array = data_file[axes[key][0]][:]
        omega_array = data_file[axes[key][1]][:]
    q_array *= measure(1.0, iunit="1/nm").toval("1/ang")
    omega_array *= measure(1.0, iunit="rad/ps", equivalent=True).toval("meV")
    is_coherent = "dcsf" in data_key
    is_incoherent = "disf" in data_key
    if not (is_coherent or is_incoherent):
        is_coherent = "Coherent" in task_name
        is_incoherent = "Incoherent" in task_name
    data_array = symmetrise_array(data_array.T).T
    omega_array = symmetrise_array(omega_array)
    sig_max = np.max(data_array)
    sig_min = np.min(data_array)
    sig_mean = np.mean(data_array)
    sig_sum = np.sum(data_array)
    q_min = np.min(q_array)
    q_max = np.max(q_array)
    omega_min = np.min(omega_array)
    omega_max = np.max(omega_array)
    result = ResultParameters(
        data_file=data_file.filename,
        signal_max=sig_max,
        signal_min=sig_min,
        signal_mean=sig_mean,
        signal_sum=sig_sum,
        q_max=q_max,
        q_min=q_min,
        E_max=omega_max,
        E_min=omega_min,
        n_q=len(q_array),
        n_E=len(omega_array),
        coh_or_inc="coherent"
        if is_coherent
        else "incoherent"
        if is_incoherent
        else "unknown",
    )
    return result, (data_array, q_array, omega_array)


class McStasSample(IJob):
    """Converts a simulation result to a McStas sample file."""

    label = "McStas Sample"

    category = ("Postprocessing",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["dsf_input_file"] = (
        "HDFInputFileConfigurator",
        {"label": "MDANSE Dynamic Structure Factor", "default": "dcsf_or_disf.mda"},
    )
    settings["output_files"] = ("OutputSqwConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()
        self.numberOfSteps = 0

        trajectory_params = get_trajectory_info(self.trajectory)
        result_params, self.result_arrays = get_result_info(
            self.configuration["dsf_input_file"]["instance"]
        )

        # need to get selection from results and use it to calculate system properties?

        self.header = create_header(trajectory_params, result_params)

    def run_step(self, index):
        """
        Skipped here.
        """
        return index, None

    def combine(self, index, x):
        """Also skipped."""

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        PLATFORM.create_directory(
            Path(self.configuration["output_files"]["file"]).parent
        )
        data_array, q_array, omega_array = self.result_arrays
        with open(self.configuration["output_files"]["file"], "w") as target:
            target.write(self.header)
            target.write("#\n")
            target.write(
                f"# WAVEVECTOR vector of m={len(q_array)} values {q_array.min()}:{q_array.max()} in [Angstroem-1]: q\n"
            )
            target.write(" ".join(str(qval) for qval in q_array) + "\n")
            target.write(
                f"# ENERGY vector of n={len(omega_array)} values {omega_array.min()}:{omega_array.max()} in [meV]: w\n"
            )
            target.write(" ".join(str(omega) for omega in omega_array) + "\n")
            target.write(
                f"# matrix of S(q,w) values (m={data_array.shape[0]} rows x n={data_array.shape[1]} columns), one row per q value: sqw\n"
            )
            target.writelines(
                " ".join([str(num) for num in row]) + "\n" for row in data_array
            )
        super().finalize()

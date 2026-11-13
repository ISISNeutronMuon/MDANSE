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

# ruff: file-ignore[T201]

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import h5py

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.IO.AtomInfo import atom_info
from MDANSE.MolecularDynamics.Trajectory import (
    Trajectory,
    check_hdf5_driver,
    chemical_system_summary,
    trajectory_summary,
)


def get_hdf5_contents(file_object: h5py.File):
    key_list = []

    def save_key(name, obj):
        if isinstance(obj, h5py.Dataset):
            key_list.append(name)

    file_object.visititems(save_key)
    return key_list


def show_trajectory_contents(args: Namespace):
    trajectory_path = args.file_name
    if not trajectory_path:
        return
    trajectory_name = Path.cwd() / trajectory_path
    instance = (
        Trajectory(trajectory_name, hdf5_driver="core")
        if check_hdf5_driver()
        else Trajectory(trajectory_name)
    )
    result = trajectory_summary(instance)
    result += chemical_system_summary(instance.chemical_system)
    traj_arrays = get_hdf5_contents(instance.file)
    result += "====DATA ARRAYS====\n"
    result += "\n".join(
        f"{name}: type={instance.file[name].dtype}, shape={instance.file[name].shape}"
        for name in traj_arrays
    )
    print(result)


def show_results_contents(filename: str, *, verbose: bool) -> None:
    text = str(filename) + "\n"
    with h5py.File(filename) as source:
        text += "===HEADER===\n"
        if verbose:
            for attr in source.attrs:
                text += f"{attr}: {source.attrs[attr]}\n"
        else:
            for attr in source.attrs:
                text += f"{attr}\n"
                for line in source.attrs[attr].split("\n"):
                    if "=" in line:
                        text += line[:80] + "\n"
        text += "===DATASETS===\n"
        for key in get_hdf5_contents(source):
            text += f"{key}: type={source[key].dtype}, shape={source[key].shape}\n"
        if not verbose:
            text += "\n The header output was truncated. Use verbose for full output\n"
    print(text)


def show_jobs(*, show_converters: bool = False):
    if show_converters:
        converters = Converter.available_names()
        output = "\n".join(
            [
                "==Converters==",
                *sorted(converters),
            ]
        )
    else:
        analyses = []
        for job_name in IJob.available_names():
            instance = IJob.create(job_name)
            if instance.category[0] != "Converters" and instance.enabled:
                analyses.append([*getattr(instance, "category", []), job_name])
        output = "\n".join(
            [
                "==Analysis==",
                *sorted(" -> ".join(analysis[1:]) for analysis in analyses),
            ]
        )
    print(output)


def show_single_job(job_name: str):
    if job_name in IJob.available_names():
        instance = IJob.create(job_name)
    elif job_name in Converter.available_names():
        instance = Converter.create(job_name)
    else:
        raise KeyError(f"{job_name} is not a converter or analysis included in MDANSE.")
    result = f"{job_name}\n"
    result += "~" * len(job_name) + "\n\n"
    if instance.__doc__:
        result += "\n".join(str(x).lstrip() for x in instance.__doc__.split("\n"))
    if not result.endswith("\n"):
        result += "\n"
    result += "\nInputs:\n\n"
    parameters = instance.get_default_parameters()
    # tab_fmt = "{:<20}{!s:>40}{!s:>10}"
    for iname, (ival, ilabel) in parameters.items():
        result += f"- {iname!s:<25}: default={ival!s:<50} # {ilabel!s:>25}\n"
    print(result)


def save_job(
    input_job_name: str | None,
    trajectory_path: str | Path | None = None,
    script_name: str | Path | None = None,
):
    job = IJob.create(input_job_name)
    if trajectory_path:
        job.configure(trajectory=trajectory_path)
    if not script_name:
        script_name = f"script_template_{input_job_name}.py"
    job.save(script_name)
    print(f"Script has been saved as {script_name}")


def save_converter(
    input_job_name: str | None,
    script_name: str | Path | None = None,
):
    job = Converter.create(input_job_name)
    if not script_name:
        script_name = f"script_template_{input_job_name}.py"
    job.save(script_name)
    print(f"Script has been saved as {script_name}")


def execute_element(args: Namespace):
    element = args.name
    database = Trajectory(args.traj) if args.traj else ATOMS_DATABASE
    match_str = args.search
    list_flag = args.list
    if list_flag:
        std_output = database.atoms
    elif match_str:
        std_output = [name for name in database.atoms if element in name]
        if not std_output:
            std_output = (
                f"No element names containing the string '{element}' were found."
            )
    elif database.has_atom(element):
        std_output = atom_info(element, database=database)
    else:
        std_output = f"Element {element} is not the atom database."
    print(std_output)


def execute_converter(args: Namespace):
    if args.list:
        show_jobs(show_converters=True)
        return
    if args.name and args.output:
        save_converter(args.name, script_name=args.output)
        return
    if args.name:
        show_single_job(args.name)


def execute_analysis(args: Namespace):
    if args.traj:
        raise NotImplementedError(
            "Setting up a script for a specific trajectory is not possible at the moment."
        )
    if args.list:
        show_jobs()
        return
    if args.name and args.output:
        save_job(args.name, trajectory_path=args.traj, script_name=args.output)
        return
    if args.name:
        show_single_job(args.name)


def execute_results(args: Namespace):
    show_results_contents(args.file_name, verbose=args.verbose)

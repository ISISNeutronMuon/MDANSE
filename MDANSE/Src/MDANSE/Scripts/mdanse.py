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

from argparse import ArgumentParser, Namespace
from pathlib import Path

import h5py

import MDANSE
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.Databases import atom_info
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Formats.HDFFormat import check_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import (
    Trajectory,
    chemical_system_summary,
    trajectory_summary,
)


class CommandLineParserError(Error):
    pass


def show_element_info(element):
    if element:
        print(ATOMS_DATABASE.info(element))  # noqa: T201


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
    instance = Trajectory(trajectory_name)
    result = trajectory_summary(instance)
    result += chemical_system_summary(instance.chemical_system)
    traj_arrays = get_hdf5_contents(instance.file)
    result += "====DATA ARRAYS====\n"
    result += "\n".join(
        f"{name}: type={instance.file[name].dtype}, shape={instance.file[name].shape}"
        for name in traj_arrays
    )
    print(result)  # noqa: T201


def show_results_contents(filename: str, *, verbose: bool) -> str:
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
            text += (
                "\n The header output was truncated. Use --verbose for full output\n"
            )
    print(text)  # noqa: T201


def show_jobs(*, show_converters: bool = False):
    if show_converters:
        converters = Converter.indirect_subclasses()
        output = "\n".join(
            [
                "==Converters==",
                *sorted(converters),
            ]
        )
    else:
        analyses = []
        for job_name in IJob.indirect_subclasses():
            instance = IJob.create(job_name)
            if instance.category[0] != "Converters" and instance.enabled:
                analyses.append(list(getattr(instance, "category", [])) + [job_name])
        output = "\n".join(
            [
                "==Analysis==",
                *sorted(" -> ".join(analysis[1:]) for analysis in analyses),
            ]
        )
    print(output)  # noqa: T201


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


def execute_element(args: Namespace):
    element = args.element_name
    database = Trajectory(args.traj) if args.traj else ATOMS_DATABASE
    match_str = args.search
    list_flag = args.list
    if list_flag:
        if hasattr(database, "atoms_in_database"):
            std_output = database.atoms_in_database
        else:
            std_output = database.atoms
    elif match_str:
        std_output = [name for name in database.atoms if match_str in name]
    elif element != "Xx":
        std_output = atom_info(element, database=database)
    else:
        std_output = f"Nothing to do for atom {element}."
    print(std_output)  # noqa: T201


def execute_converter(args: Namespace):
    if args.list:
        show_jobs(show_converters=True)
        return


def execute_analysis(args: Namespace):
    if args.list:
        show_jobs()
        return


def execute_results(args: Namespace):
    show_results_contents(args.file_name, verbose=args.verbose)


def build_parsers() -> ArgumentParser:
    parser = ArgumentParser(
        prog="mdanse",
        description="This is the command line interface of MDANSE "
        "(Molecular Dynamics Analysis for Neutron Scattering Experiments).",
        epilog="Please report any problems with MDANSE as issues on https://github.com/ISISNeutronMuon/MDANSE",
    )
    subparsers = parser.add_subparsers(title="MDANSE CLI Commands")
    # Set up element options.
    element = subparsers.add_parser(
        "element",
        help="View chemical element information.",
        description="MDANSE stores chemical element properties in a central database. "
        "When you convert trajectories, the properties of the relevant atoms are written into the trajectory file. "
        "This command can be used to list, find and view atom properties in specific files.",
    )
    element.add_argument(
        "element_name",
        help="Symbol of the chemical element or isotope, e.g. Au, Li7, etc.",
        default="Xx",
    )
    element.add_argument(
        "-t", "--traj", help="Use this trajectory file as atom database."
    )
    element.add_argument(
        "-s", "--search", help="Find chemical elements with matching names."
    )
    element.add_argument(
        "-l",
        "--list",
        action="store_true",
        default=False,
        help="List all the chemical elements in the database.",
    )
    # Set up trajectory options.
    trajectory = subparsers.add_parser(
        "traj",
        help="View contents of a trajectory file.",
        description="MDANSE stores trajectories as binary HDF5 files (.mdt). "
        "This command allows you to view the contents of a trajectory file.",
    )
    trajectory.add_argument(
        "file_name", help="Path to the trajectory file, e.g. converted_dlpoly_run.mdt"
    )
    # Set up results options.
    results = subparsers.add_parser(
        "results",
        help="View contents of a result file.",
        description="This command allows you to check what analysis types are available in MDANSE "
        "and to create analysis scripts for a given analysis type and trajectory file.",
    )
    results.add_argument(
        "file_name", help="Path to the results file, e.g. dcsf_h2o_200K.mda"
    )
    results.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Show the full contents each header entry. False by default.",
    )
    # Set up converter options.
    converter = subparsers.add_parser(
        "convert",
        help="Create a script to convert MD output into an MDANSE .mdt file.",
    )
    converter.add_argument(
        "-l",
        "--list",
        action="store_true",
        default=False,
        help="List all the converter types.",
    )
    converter.add_argument(
        "-n", "--name", help="Name of the specific converter to be used."
    )
    converter.add_argument(
        "-o",
        "--output",
        default="converter_script.py",
        help="Use this file name for the output Python script.",
    )
    # Set up analysis options.
    analysis = subparsers.add_parser(
        "analysis",
        help="Create a script to analyse an MD trajectory.",
        description="This command allows you to check what analysis types are available in MDANSE "
        "and to create analysis scripts for a given analysis type and trajectory file.",
    )
    analysis.add_argument(
        "-l",
        "--list",
        action="store_true",
        default=False,
        help="List all the analysis types.",
    )
    analysis.add_argument(
        "-n", "--name", help="Name of the specific analysis to be used."
    )
    analysis.add_argument(
        "-t", "--traj", help="Use this trajectory file as analysis input."
    )
    analysis.add_argument(
        "-o",
        "--output",
        default="analyis_script.py",
        help="Use this file name for the output Python script.",
    )
    # Add handler functions to parsers:
    for subparser, function in [
        (element, execute_element),
        (trajectory, show_trajectory_contents),
        (converter, execute_converter),
        (analysis, execute_analysis),
        (results, execute_results),
    ]:
        subparser.set_defaults(func=function)
    return parser


def main():
    parser = build_parsers()

    args: Namespace = parser.parse_args()
    if not vars(args):
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()

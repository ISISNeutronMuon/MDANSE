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

import textwrap
from argparse import (
    ArgumentParser,
    Namespace,
    RawDescriptionHelpFormatter,
    _SubParsersAction,
)
from pathlib import Path
from typing import Any

import h5py

import MDANSE
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Formats.HDFFormat import check_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.IO.AtomInfo import atom_info
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
                analyses.append([*getattr(instance, "category", []), job_name])
        output = "\n".join(
            [
                "==Analysis==",
                *sorted(" -> ".join(analysis[1:]) for analysis in analyses),
            ]
        )
    print(output)  # noqa: T201


def show_single_job(job_name: str):
    if job_name in IJob.indirect_subclasses():
        instance = IJob.create(job_name)
    elif job_name in Converter.indirect_subclasses():
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
    print(result)  # noqa: T201


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
    print(f"Script has been saved as {script_name}")  # noqa: T201


def save_converter(
    input_job_name: str | None,
    script_name: str | Path | None = None,
):
    job = Converter.create(input_job_name)
    if not script_name:
        script_name = f"script_template_{input_job_name}.py"
    job.save(script_name)
    print(f"Script has been saved as {script_name}")  # noqa: T201


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
    print(std_output)  # noqa: T201


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


def _converter_parser(subparsers: _SubParsersAction) -> Any:
    """Set up converter input options."""
    converter = subparsers.add_parser(
        "convert",
        help="Create a script to convert MD output into an MDANSE .mdt file.",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        MDANSE converts trajectories from different formats
        to a binary HDF5 file with an .mdt extension.
        Different converters are available in MDANSE,
        depending on the MD engine used to run the simulation.

        Examples
        --------
            mdanse convert -l
                Shows the list of all the available converters.
            mdanse convert CP2K
                Shows the description of the CP2K converter.
            mdanse convert CP2K -o mdanse_cp2k_script.py
                Saves a CP2K conversion script with default input values as mdanse_cp2K_script.py
        """
        ),
    )
    converter.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all the converter types.",
    )
    converter.add_argument(
        "name", nargs="?", help="Name of the specific converter to be used."
    )
    converter.add_argument(
        "-o",
        "--output",
        help="Use this file name for the output Python script.",
    )
    return converter


def _analysis_parser(subparsers: _SubParsersAction) -> Any:
    """Set up analysis input options."""
    analysis = subparsers.add_parser(
        "analysis",
        help="Create a script to analyse an MD trajectory.",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        MDANSE can perform different analysis types on .mdt trajectories.
        mdanse analysis commands let you view the available analysis types,
        and create analysis scripts which you can run after adjusting the parameters.

        Examples:
        ---------
            mdanse analysis -l
                Shows the list of all the available analysis types.
            mdanse analysis DensityOfStates
                Shows the description of the density of states analysis.
            mdanse analysis DensityOfStates -o mdanse_dos_script.py
                Saves a density of states script with default input values as mdanse_dos_script.py
        """
        ),
    )
    analysis.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all the analysis types.",
    )
    analysis.add_argument(
        "name", nargs="?", help="Name of the specific analysis to be used."
    )
    analysis.add_argument(
        "-t", "--traj", help="Use this trajectory file as analysis input."
    )
    analysis.add_argument(
        "-o",
        "--output",
        default=None,
        help="Use this file name for the output Python script.",
    )
    return analysis


def _trajectory_parser(subparsers: _SubParsersAction) -> Any:
    """Set up trajectory input options."""
    trajectory = subparsers.add_parser(
        "traj",
        help="View contents of a trajectory file.",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        MDANSE stores trajectories as binary HDF5 files (.mdt).
        'mdanse traj' allows you to view the contents of a trajectory file.
        The information includes chemical composition, number of steps,
        data arrays in the file (positions, velocities, etc.).

        Examples:
        ---------
            mdanse traj hexane_CP2K_157K.mdt
                Shows information about the trajectory hexane_CP2K_157K.mdt
        """
        ),
    )
    trajectory.add_argument(
        "file_name", help="Path to the trajectory file, e.g. converted_dlpoly_run.mdt"
    )
    return trajectory


def _results_parser(subparsers: _SubParsersAction) -> Any:
    """Set up results input options."""
    results = subparsers.add_parser(
        "results",
        help="View contents of a result file.",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        MDANSE results are normally written to an HDF5 file with an .mda extension.
        These are binary files, and cannot be viewed immediately with a text editor.
        mdanse results command can be used to quickly check what information has
        been written to an .mda file.

        Examples:
        ---------
            mdanse results dos_BaTiO3_250K.mda
                Shows the names of header entries and datasets in the file dos_BaTiO3_250K.mda
            mdanse results -v dos_BaTiO3_250K.mda
                Shows the full header information and dataset names in the file dos_BaTiO3_250K.mda
        """
        ),
    )
    results.add_argument(
        "file_name", help="Path to the results file, e.g. dcsf_h2o_200K.mda"
    )
    results.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show the full contents each header entry. False by default.",
    )
    return results


def _element_parser(subparsers: _SubParsersAction) -> Any:
    """Set up element input options."""
    element = subparsers.add_parser(
        "element",
        help="View chemical element information.",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        MDANSE has its own database of chemical elements, which
        can be modified and extended by users.
        When you convert trajectories, the properties of the relevant atoms
        are written into the trajectory file from the current version of
        the database.
        You can view the atom properties in the database and in the trajectory
        files using the 'mdanse element' command.

        Examples:
        ---------
            mdanse element Au
                Shows the properties of gold (Au) stored in the MDANSE database.
            mdanse element --traj some_AuAg_alloy.mdt Au
                Shows the properties of gold (Au) stored in the trajectory file.
            mdanse element -s Li
                Shows all the elements with 'Li' in their name (e.g. Li, Li6, Li7)
        """
        ),
    )
    element.add_argument(
        "name",
        help="Symbol of the chemical element or isotope, e.g. Au, Li7, etc.",
        nargs="?",
    )
    element.add_argument(
        "-t", "--traj", help="Use this trajectory file as atom database."
    )
    element.add_argument(
        "-s",
        "--search",
        action="store_true",
        help="Find chemical elements with matching names.",
    )
    element.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all the chemical elements in the database.",
    )
    return element


def build_parsers() -> ArgumentParser:
    parser = ArgumentParser(
        prog="mdanse",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
        This is the command line interface of MDANSE
        (Molecular Dynamics Analysis for Neutron Scattering Experiments).
        The usual MDANSE workflow consists of converting the trajectory,
        running an analysis and viewing the results.

        Find out more about specific subcommands by running:
        mdanse convert -h
        mdanse analysis -h
        mdanse traj -h
        mdanse results -h
        mdanse element -h
        """
        ),
        epilog="Please report any problems with MDANSE as issues on https://github.com/ISISNeutronMuon/MDANSE",
    )
    subparsers = parser.add_subparsers(
        title="MDANSE CLI Commands",
        help="Run each command with -h to see input options.",
    )
    # Add handler functions to parsers:
    for subparser, function in [
        (_element_parser(subparsers), execute_element),
        (_trajectory_parser(subparsers), show_trajectory_contents),
        (_converter_parser(subparsers), execute_converter),
        (_analysis_parser(subparsers), execute_analysis),
        (_results_parser(subparsers), execute_results),
    ]:
        subparser.set_defaults(func=function)
    return parser


def main():
    LOG.setLevel("INFO")
    parser = build_parsers()

    args: Namespace = parser.parse_args()
    if not vars(args):
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()

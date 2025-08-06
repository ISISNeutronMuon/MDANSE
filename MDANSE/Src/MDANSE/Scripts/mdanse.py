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

import MDANSE
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class CommandLineParserError(Error):
    pass


def show_element_info(args: Namespace):
    element = args.element_name
    if element:
        print(ATOMS_DATABASE.info(element))  # noqa: T201


def show_trajectory_contents(args: Namespace):
    trajectory_path = args.file_name
    if not trajectory_path:
        return
    trajName = Path.cwd() / trajectory_path
    inputTraj = Trajectory(trajName)
    print(str(inputTraj))  # noqa: T201


def show_jobs(input_job_name: str | None = None):
    if input_job_name is None:
        return
    if not input_job_name:
        print("Registered jobs:")  # noqa: T201
        converters = []
        analyses = []
        for job_name in IJob.indirect_subclasses():
            instance = IJob.create(job_name)
            if instance.category[0] == "Converters":
                converters.append(job_name)
            else:
                analyses.append(list(getattr(instance, "category", [])) + [job_name])
        output = "\n".join(
            [
                "==Converter==",
                *sorted(converters),
                "==Analysis==",
                *sorted(" -> ".join(analysis[1:]) for analysis in analyses),
            ]
        )
        print(output)  # noqa: T201
    else:
        print(IJob.create(input_job_name).info)  # noqa: T201


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
    element.set_defaults(func=show_element_info)
    element.add_argument(
        "element_name",
        help="Symbol of the chemical element or isotope, e.g. Au, Li7, etc.",
    )
    element.add_argument(
        "-t", "--traj", help="Use this trajectory file as atom database."
    )
    element.add_argument(
        "-s", "--search", help="Find chemical elements with matching names."
    )
    element.add_argument(
        "-l", "--list", help="List all the chemical elements in the database."
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
    trajectory.set_defaults(func=show_trajectory_contents)
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
    results.set_defaults(func=show_trajectory_contents)
    # Set up converter options.
    converter = subparsers.add_parser(
        "converter",
        help="Create a script to convert MD output into an MDANSE .mdt file.",
    )
    converter.add_argument("-l", "--list", help="List all the converter types.")
    converter.add_argument(
        "-n", "--name", help="Name of the specific converter to be used."
    )
    converter.add_argument(
        "-o", "--output", help="Use this file name for the output Python script."
    )
    # Set up analysis options.
    analysis = subparsers.add_parser(
        "analysis",
        help="Create a script to analyse an MD trajectory.",
        description="This command allows you to check what analysis types are available in MDANSE "
        "and to create analysis scripts for a given analysis type and trajectory file.",
    )
    analysis.add_argument("-l", "--list", help="List all the analysis types.")
    analysis.add_argument(
        "-n", "--name", help="Name of the specific analysis to be used."
    )
    analysis.add_argument(
        "-t", "--traj", help="Use this trajectory file as analysis input."
    )
    analysis.add_argument(
        "-o", "--output", help="Use this file name for the output Python script."
    )
    # Everything has been set up.
    return parser


def main():
    parser = build_parsers()

    args: Namespace = parser.parse_args()
    if not vars(args):
        parser.print_usage()
    else:
        args.func(args)


if __name__ == "__main__":
    main()

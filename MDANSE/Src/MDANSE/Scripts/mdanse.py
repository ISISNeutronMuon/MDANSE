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

from argparse import ArgumentParser
from pathlib import Path

import MDANSE
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class CommandLineParserError(Error):
    pass


def show_element_info(element: str | None):
    if element:
        print(ATOMS_DATABASE.info(element))  # noqa: T201


def show_trajectory_contents(trajectory_path: str | Path | None):
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


def produce_output(options: dict[str, str], args: list[str]):
    print(options)
    show_element_info(options.element)
    show_trajectory_contents(options.trajectory)
    show_jobs(options.job)


def main():
    parser = ArgumentParser(
        prog="MDANSE CLI",
        description="This is the command line interface of MDANSE "
        "(Molecular Dynamics Analysis for Neutron Scattering Experiments).",
        epilog="Please report any problems with MDANSE as issues on https://github.com/ISISNeutronMuon/MDANSE",
    )
    parser.add_argument("-t", "--traj")
    subparsers = parser.add_subparsers(title="MDANSE CLI Commands")
    element = subparsers.add_parser(
        "element", help="View chemical element information."
    )
    trajectory = subparsers.add_parser(
        "traj", help="View contents of a trajectory file."
    )
    analysis = subparsers.add_parser("analysis")
    param_group = parser.add_argument_group("Input parameters")

    parser.parse_args()


if __name__ == "__main__":
    main()

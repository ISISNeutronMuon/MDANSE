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

from optparse import IndentedHelpFormatter, OptionGroup, OptionParser
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


def produce_output(options: Values, args: list[str]):
    show_element_info(options.element)
    show_trajectory_contents(options.trajectory)
    show_jobs(options.job)


def main():
    parser = OptionParser(
        formatter=IndentedHelpFormatter(), version=f"MDANSE {MDANSE.__version__} "
    )
    param_group = OptionGroup(
        parser, "Input Parameters", "Here you can input atom or file names."
    )
    param_group.add_option(
        "-e",
        "--element",
        action="store",
        type="str",
        dest="element",
        help="Name of the chemical element to be displayed.",
    )
    param_group.add_option(
        "-j",
        "--job",
        action="store",
        type="str",
        dest="job",
        help="Name of the MDANSE converter or analysis to be used.",
    )
    param_group.add_option(
        "-t",
        "--traj",
        action="store",
        type="str",
        dest="trajectory",
        help="Name of the trajectory file which will be used.",
    )
    parser.add_option_group(param_group)
    command_group = OptionGroup(
        parser, "Commands", "These options tell MDANSE what to do."
    )
    command_group.add_option(
        "-s",
        action="store_true",
        dest="save_script",
        default=False,
        help="Save a job script with default parameters for the specified trajectory.",
        metavar="MDANSE_SCRIPT",
    )
    command_group.add_option(
        "-i",
        action="store_true",
        dest="show_info",
        default=False,
        help="Save a job template.",
        metavar="MDANSE_SCRIPT",
    )
    parser.add_option_group(command_group)

    # The command line is parsed.
    options, args = parser.parse_args()
    produce_output(options, args)


if __name__ == "__main__":
    main()

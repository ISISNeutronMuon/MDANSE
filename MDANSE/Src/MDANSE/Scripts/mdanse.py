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

import textwrap
from argparse import (
    ArgumentParser,
    Namespace,
    RawDescriptionHelpFormatter,
    _SubParsersAction,
)
from pathlib import Path
from typing import Any

import MDANSE
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Platform import PLATFORM, version_summary
from MDANSE.MLogging import LOG
from MDANSE.Scripts.tui import MDANSETui

from .funcs import (
    execute_analysis,
    execute_converter,
    execute_element,
    execute_results,
    show_trajectory_contents,
)


class CommandLineParserError(Exception):
    pass


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


def _tui_parser(subparsers: _SubParsersAction) -> Any:
    tui = subparsers.add_parser(
        "tui",
        help="Start the MDANSE text user interface (TUI).",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Start the interactive TUI environment of MDANSE allowing you to
            run various calculations.

            For more information
        """
        ),
    )
    return tui


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
        mdanse tui -h
        mdanse convert -h
        mdanse analysis -h
        mdanse traj -h
        mdanse results -h
        mdanse element -h
        """
        ),
        epilog="Please report any problems with MDANSE as issues on https://github.com/ISISNeutronMuon/MDANSE",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{version_summary(show_backend=False)}",
    )
    settings_group = parser.add_mutually_exclusive_group()
    settings_group.add_argument(
        "--settings",
        help="Settings folder to use.",
        default=None,
    )
    settings_group.add_argument(
        "--local",
        help="Use local settings.",
        action="store_true",
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
        (_tui_parser(subparsers), MDANSETui().cmdloop),
    ]:
        subparser.set_defaults(func=function)
    return parser


def main():
    LOG.setLevel("INFO")
    print(f"MDANSE version {MDANSE.__version__}")
    parser = build_parsers()
    args: Namespace = parser.parse_args()

    # Override settings directories.
    if args.local:
        PLATFORM._application_directory = Path.cwd()
    if args.settings:
        PLATFORM._application_directory = Path(args.settings)

    # Reload databases with new paths.
    ATOMS_DATABASE._load()

    if not hasattr(args, "func"):
        MDANSETui().cmdloop()
    else:
        args.func(args)


if __name__ == "__main__":
    main()

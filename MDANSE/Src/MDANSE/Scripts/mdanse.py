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

import sys
from optparse import IndentedHelpFormatter, OptionGroup, OptionParser
from pathlib import Path

from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.JobStatus import JobInfo
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class CommandLineParserError(Error):
    pass


class CommandLineParser(OptionParser):
    """A sublcass of OptionParser.

    Creates the MDANSE commad line parser.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def display_element_info(self, option, opt_str, value, parser):
        if len(parser.rargs) != 1:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

        element = parser.rargs[0]

        from MDANSE.Chemistry import ATOMS_DATABASE

        try:
            print(ATOMS_DATABASE.info(element))  # noqa: T201
        except ValueError:
            raise CommandLineParserError(
                f"The entry {element!r} is not registered in the database"
            )

    def display_trajectory_contents(self, option, opt_str, value, parser):
        """Displays trajectory contents

        @param option: the option that triggered the callback.
        @type option: optparse.Option instance

        @param opt_str: the option string seen on the command line.
        @type opt_str: str

        @param value: the argument for the option.
        @type value: str

        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        """

        trajName = parser.rargs[0]
        inputTraj = Trajectory(trajName)
        print(str(inputTraj))  # noqa: T201

    def error(self, msg):
        """Called when an error occured in the command line.

        @param msg: the error message.
        @type msg: str
        """

        self.print_help(sys.stderr)
        self.exit(2, f"Error: {msg}\n")

    def query_classes_registry(self, option, opt_str, value, parser):
        """
        Callback that displays the list of the jobs available in MDANSE

        @param option: the Option instance calling the callback.

        @param opt_str: the option string seen on the command-line triggering the callback

        @param value: the argument to this option seen on the command-line.

        @param parser: the MDANSEOptionParser instance.
        """

        if len(parser.rargs) == 0:
            print("Registered jobs:")  # noqa: T201
            for interfaceName in IJob.indirect_subclasses():
                print("\t- %s", interfaceName)  # noqa: T201
        elif len(parser.rargs) == 1:
            val = parser.rargs[0]
            print(IJob.create(val).info())  # noqa: T201
        else:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

    def save_job(self, option, opt_str, value, parser):
        """
        Save job templates.

        @param option: the option that triggered the callback.
        @type option: optparse.Option instance

        @param opt_str: the option string seen on the command line.
        @type opt_str: str

        @param value: the argument for the option.
        @type value: str

        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        """

        if len(parser.rargs) != 1:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

        jobs = IJob

        name = parser.rargs[0]

        # A name for the template is built.
        filename = Path(f"template_{name.lower()}.py").absolute()

        # Try to save the template for the job.
        try:
            jobs.create(name).save(filename)
        # Case where an error occured when writing the template.
        except OSError:
            raise CommandLineParserError(
                f"Could not write the job template as {filename!r}"
            )
        # If the job class has no save method, thisis not a valid MDANSE job.
        except KeyError:
            raise CommandLineParserError(f"The job {name!r} is not a valid MDANSE job")
        # Otherwise, print some information about the saved template.
        else:
            print("Saved template for job %r as %r", name, filename)  # noqa: T201

    def save_job_template(self, option, opt_str, value, parser):
        """
        Save job templates.

        @param option: the option that triggered the callback.
        @type option: optparse.Option instance

        @param opt_str: the option string seen on the command line.
        @type opt_str: str

        @param value: the argument for the option.
        @type value: str

        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        """

        nargs = len(parser.rargs)

        from MDANSE.Framework.Jobs.IJob import IJob

        if nargs != 2:
            LOG.error(
                "Two arguments required resp. the name and the shortname of the class to be templated"
            )
            return

        classname, shortname = parser.rargs

        try:
            IJob.save_template(shortname, classname)
        except (OSError, KeyError):
            return


def main():
    import MDANSE

    # Creates the option parser.
    parser = CommandLineParser(
        formatter=IndentedHelpFormatter(), version=f"MDANSE {MDANSE.__version__} "
    )

    # Creates a first the group of general options.
    group = OptionGroup(parser, "General options")
    group.add_option(
        "-d",
        "--database",
        action="callback",
        callback=parser.display_element_info,
        help="Display chemical informations about a given element.",
    )
    group.add_option(
        "-r",
        "--registry",
        action="callback",
        callback=parser.query_classes_registry,
        help="Display the contents of MDANSE classes registry.",
    )
    group.add_option(
        "-t",
        "--traj",
        action="callback",
        callback=parser.display_trajectory_contents,
        help="Display the chemical contents of a trajectory.",
    )

    # Add the goup to the parser.
    parser.add_option_group(group)

    # Creates a second group of job-specific options.
    group = OptionGroup(parser, "Job managing options")

    # Add the goup to the parser.
    parser.add_option_group(group)

    group.add_option(
        "--js",
        action="callback",
        callback=parser.save_job,
        help="Save a job script with default patameters.",
        metavar="MDANSE_SCRIPT",
    )
    group.add_option(
        "--jt",
        action="callback",
        callback=parser.save_job_template,
        help="Save a job template.",
        metavar="MDANSE_SCRIPT",
    )

    # The command line is parsed.
    options, _ = parser.parse_args()


if __name__ == "__main__":
    main()

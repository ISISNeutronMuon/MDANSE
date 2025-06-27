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
import optparse
import pickle
import subprocess
import sys
import textwrap
from pathlib import Path

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.JobStatus import JobInfo
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class IndentedHelp(optparse.IndentedHelpFormatter):
    """This class modify slightly the help formatter of the optparse.OptionParser class.

    This allows to take into account the line feed properly.

    @note: code taken as it is from an implementation made by Tim Chase
    (http://groups.google.com/group/comp.lang.python/browse_thread/thread/6df6e6b541a15bc2/09f28e26af0699b1)
    """

    def format_description(self, description):
        if not description:
            return ""
        desc_width = self.width - self.current_indent
        indent = " " * self.current_indent
        bits = description.splitlines()
        formatted_bits = (
            textwrap.fill(
                bit, desc_width, initial_indent=indent, subsequent_indent=indent
            )
            for bit in bits
        )
        result = "\n".join(formatted_bits) + "\n"

        return result

    def format_option(self, option):
        indent = " " * self.current_indent
        result = ""
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = f"{indent}{opts}\n"
            indent_first = self.help_position
        else:  # start help on same line as opts
            opts = f"{indent}{opts}  "
            indent_first = 0
        result += opts
        if option.help:
            help_text = self.expand_default(option)
            # Everything is the same up through here
            help_lines = [
                textwrap.wrap(para, self.help_width) for para in help_text.splitlines()
            ]
            # Everything is the same after here
            result += f"{indent_first}{help_lines[0]}\n"
            result += (
                "\n".join(
                    f"{' ' * self.help_position}{line}" for line in help_lines[1:]
                )
                + "\n"
            )
        elif not opts.endswith("\n"):
            result += "\n"

        return result


class CommandLineParserError(Error):
    pass


class CommandLineParser(optparse.OptionParser):
    """A sublcass of OptionParser.

    Creates the MDANSE commad line parser.
    """

    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, *args, **kwargs)

    def check_job(self, option, opt_str, value, parser):
        """Display the jobs list

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

        basename = parser.rargs[0]

        filename = PLATFORM.temporary_files_directory() / basename

        if not filename.exists():
            raise CommandLineParserError("Invalid job name")

        # Open the job temporary file
        try:
            f = open(filename, "rb")
            info = pickle.load(f)
            f.close()

        # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
        except Exception:
            raise CommandLineParserError(
                f"The job {basename!r} could not be opened properly."
            )

        # The job file could be opened and unpickled properly
        else:
            # Check that the unpickled object is a JobStatus object
            if not isinstance(info, JobInfo):
                raise CommandLineParserError(f"Invalid contents for job {basename!r}.")

            LOG.info("Information about %s job:", basename)
            for k, v in info.items():
                LOG.info("%-20s [%s]", k, v)

    def display_element_info(self, option, opt_str, value, parser):
        if len(parser.rargs) != 1:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

        element = parser.rargs[0]

        from MDANSE.Chemistry import ATOMS_DATABASE

        try:
            LOG.info(ATOMS_DATABASE.info(element))
        except ValueError:
            raise CommandLineParserError(
                f"The entry {element!r} is not registered in the database"
            )

    def display_jobs_list(self, option, opt_str, value, parser):
        """Display the jobs list

        @param option: the option that triggered the callback.
        @type option: optparse.Option instance

        @param opt_str: the option string seen on the command line.
        @type opt_str: str

        @param value: the argument for the option.
        @type value: str

        @param parser: the MDANSE option parser.
        @type parser: instance of MDANSEOptionParser
        """

        if len(parser.rargs) != 0:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

        jobs = PLATFORM.temporary_files_directory().glob("*")

        for j in jobs:
            # Open the job temporary file
            try:
                with j.open("rb") as f:
                    info = pickle.load(f)

            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except Exception:
                continue

            # The job file could be opened and unpickled properly
            else:
                # Check that the unpickled object is a JobStatus object
                if not isinstance(info, JobInfo):
                    continue

                LOG.info("%-20s [%s]", j.stem, info["state"])

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
        LOG.info(str(inputTraj))

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
            LOG.info("Registered jobs:")
            for interfaceName in IJob.indirect_subclasses():
                LOG.info("\t- %s", interfaceName)
        elif len(parser.rargs) == 1:
            val = parser.rargs[0]
            LOG.info(IJob.create(val).info())
        else:
            raise CommandLineParserError(
                f"Invalid number of arguments for {opt_str!r} option"
            )

    def run_job(self, option, opt_str, value, parser):
        """Run job file(s).

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

        filename = Path(parser.rargs[0])

        if not filename.exists():
            raise CommandLineParserError(
                f"The job file {filename!r} could not be executed"
            )

        subprocess.Popen([sys.executable, filename])

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
            LOG.info("Saved template for job %r as %r", name, filename)

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
        formatter=IndentedHelp(), version=f"MDANSE {MDANSE.__version__} "
    )

    # Creates a first the group of general options.
    group = optparse.OptionGroup(parser, "General options")
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
    group = optparse.OptionGroup(parser, "Job managing options")

    # Add the goup to the parser.
    parser.add_option_group(group)

    group.add_option(
        "--jc",
        action="callback",
        callback=parser.check_job,
        help="Check the status of a given job.",
    )
    group.add_option(
        "--jl",
        action="callback",
        callback=parser.display_jobs_list,
        help="Display the jobs list.",
    )
    group.add_option(
        "--jr", action="callback", callback=parser.run_job, help="Run MDANSE job(s)."
    )
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

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

import pickle
import glob
import optparse
import os
import subprocess
import sys
import textwrap

from MDANSE.Core.Error import Error
from MDANSE import PLATFORM
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.JobStatus import JobState


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
        bits = description.split("\n")
        formatted_bits = [
            textwrap.fill(
                bit, desc_width, initial_indent=indent, subsequent_indent=indent
            )
            for bit in bits
        ]
        result = "\n".join(formatted_bits) + "\n"

        return result

    def format_option(self, option):
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else:  # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = self.expand_default(option)
            # Everything is the same up through here
            help_lines = []
            for para in help_text.split("\n"):
                help_lines.extend(textwrap.wrap(para, self.help_width))
            # Everything is the same after here
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(
                ["%*s%s\n" % (self.help_position, "", line) for line in help_lines[1:]]
            )
        elif opts[-1] != "\n":
            result.append("\n")

        return "".join(result)


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
                "Invalid number of arguments for %r option" % opt_str
            )

        basename = parser.rargs[0]

        filename = os.path.join(PLATFORM.temporary_files_directory(), basename)

        if not os.path.exists(filename):
            raise CommandLineParserError("Invalid job name")

        # Open the job temporary file
        try:
            f = open(filename, "rb")
            info = pickle.load(f)
            f.close()

        # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
        except:
            raise CommandLineParserError(
                "The job %r could not be opened properly." % basename
            )

        # The job file could be opened and unpickled properly
        else:
            # Check that the unpickled object is a JobStatus object
            if not isinstance(info, JobState):
                raise CommandLineParserError("Invalid contents for job %r." % basename)

            print("Information about %s job:" % basename)
            for k, v in info.iteritems():
                print("%-20s [%s]" % (k, v))

    def display_element_info(self, option, opt_str, value, parser):
        if len(parser.rargs) != 1:
            raise CommandLineParserError(
                "Invalid number of arguments for %r option" % opt_str
            )

        element = parser.rargs[0]

        from MDANSE.Chemistry import ATOMS_DATABASE

        try:
            print(ATOMS_DATABASE.info(element))
        except ValueError:
            raise CommandLineParserError(
                "The entry %r is not registered in the database" % element
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
                "Invalid number of arguments for %r option" % opt_str
            )

        jobs = [
            f
            for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(), "*"))
        ]

        for j in jobs:
            # Open the job temporary file
            try:
                f = open(j, "rb")
                info = pickle.load(f)
                f.close()

            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except:
                continue

            # The job file could be opened and unpickled properly
            else:
                # Check that the unpickled object is a JobStatus object
                if not isinstance(info, JobState):
                    continue

                print("%-20s [%s]" % (os.path.basename(j), info["state"]))

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
        inputTraj = HDFTrajectoryInputData(trajName)
        print(inputTraj.info())

    def error(self, msg):
        """Called when an error occured in the command line.

        @param msg: the error message.
        @type msg: str
        """

        self.print_help(sys.stderr)
        print("\n")
        self.exit(2, "Error: %s\n" % msg)

    def query_classes_registry(self, option, opt_str, value, parser):
        """
        Callback that displays the list of the jobs available in MDANSE

        @param option: the Option instance calling the callback.

        @param opt_str: the option string seen on the command-line triggering the callback

        @param value: the argument to this option seen on the command-line.

        @param parser: the MDANSEOptionParser instance.
        """

        if len(parser.rargs) == 0:
            print("Registered jobs:")
            for interfaceName in IJob.indirect_subclasses():
                print("\t- %s" % interfaceName)
        elif len(parser.rargs) == 1:
            val = parser.rargs[0]
            print(IJob.create(val).info())
        else:
            raise CommandLineParserError(
                "Invalid number of arguments for %r option" % opt_str
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
                "Invalid number of arguments for %r option" % opt_str
            )

        filename = parser.rargs[0]

        if not os.path.exists(filename):
            raise CommandLineParserError(
                "The job file %r could not be executed" % filename
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
                "Invalid number of arguments for %r option" % opt_str
            )

        jobs = IJob

        name = parser.rargs[0]

        # A name for the template is built.
        filename = os.path.abspath("template_%s.py" % name.lower())

        # Try to save the template for the job.
        try:
            jobs.create(name).save(filename)
        # Case where an error occured when writing the template.
        except IOError:
            raise CommandLineParserError(
                "Could not write the job template as %r" % filename
            )
        # If the job class has no save method, thisis not a valid MDANSE job.
        except KeyError:
            raise CommandLineParserError("The job %r is not a valid MDANSE job" % name)
        # Otherwise, print some information about the saved template.
        else:
            print("Saved template for job %r as %r" % (name, filename))

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
            print(
                "Two arguments required resp. the name and the shortname of the class to be templated"
            )
            return

        classname, shortname = parser.rargs

        try:
            IJob.save_template(shortname, classname)
        except (IOError, KeyError) as e:
            return


def main():
    import MDANSE

    # Creates the option parser.
    parser = CommandLineParser(
        formatter=IndentedHelp(), version="MDANSE %s " % MDANSE.__version__
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

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
import argparse
import sys

from MDANSE.MLogging import LOG


def parse_args():
    parser = argparse.ArgumentParser(
        description="""This is mdanse_job: a shortcut for running MDANSE job. It opens a GUI dialog 
    from where an analysis or a trajectory converter will be setup and eventually run."""
    )
    parser.add_argument(
        "job",
        nargs=1,
        help='Code for the job to be run. E.g. msd for Mean Square Displacement. For a complete list of available jobs please run "mdanse -r job"',
    )
    parser.add_argument(
        "trajectory",
        nargs="*",
        help="HDF Trajectory file. This is needed only for analysis job. Not required for trajectory conversion jobs.",
    )
    args = parser.parse_args()

    return args


def main():
    from MDANSE import REGISTRY
    from MDANSE.GUI.Apps import JobApp

    args = parse_args()
    trajectory = args.trajectory
    job = args.job[0]

    if job not in REGISTRY["job"]:
        LOG.error("Unknown job: %s" % job)
        sys.exit(1)

    for v in REGISTRY["job"][job].settings.values():
        if v[0] == "hdf_trajectory" and not trajectory:
            LOG.error("A trajectory is needed")
            sys.exit(1)

    trajectory = trajectory[0] if trajectory else None

    app = JobApp(job, trajectory)
    app.MainLoop()


if __name__ == "__main__":
    main()

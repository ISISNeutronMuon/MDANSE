# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import argparse
import sys


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

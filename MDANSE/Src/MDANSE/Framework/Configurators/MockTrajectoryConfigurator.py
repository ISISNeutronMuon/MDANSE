# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/MDMCTrajectoryConfigurator.py
# @brief     A way to take in a trajectory from MDMC in a wrapper
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


class MockTrajectoryConfigurator(IConfigurator):
    """
    This is a replacement for a trajectory stored in and HDF5 file.
    It is intended to be a drop-in replacement for HDFTrajectoryConfigurator,
    even though it is NOT based on an HDF5 file.
    It can use a JSON file with MockTrajectory parameters to create
    a trajectory entirely in the RAM.
    """

    _default = None

    def __init__(self, name, wildcard="JSON file|*.json", **kwargs):
        """
        Initializes the configurator object.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self._wildcard = wildcard

    def configure(self, value: str):
        """
        Configure a mock trajectory file.

        :param value: a JSON file with a MockTrajectory definition
        :type value: str
        """

        self["value"] = value
        self["filename"] = "Mock"

        self["instance"] = MockTrajectory.from_json(value)

        self["basename"] = "Mock"

        self["length"] = len(self["instance"])

        self["md_time_step"] = self["instance"]._time_step

        self["has_velocities"] = self["instance"].has_velocities

    def get_information(self):
        """
        Returns some basic informations about the contents of the HDF trajectory file.

        :return: the informations about the contents of the HDF trajectory file.
        :rtype: str
        """

        info = ["Mock trajectory used as input"]
        info.append("Number of steps: %d\n" % self["length"])
        info.append(
            "Size of the chemical system: %d\n"
            % self["instance"].chemical_system.number_of_atoms
        )
        if self["has_velocities"]:
            info.append("The trajectory contains atomic velocities\n")
        else:
            info.append("The trajectory does not contain atomic velocities\n")

        return "".join(info)

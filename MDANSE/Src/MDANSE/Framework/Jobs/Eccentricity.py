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

import collections

import numpy as np


from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class Eccentricity(IJob):
    """
    Computes the eccentricity for a set of atoms e.g. in a micelle.\n

    **Calculation:** \n
    Eccentricity is calculated using the principal axes of inertia 'I' along x, y and z: \n
    .. math:: Eccentricity = 1-\\frac{I_{min}}{I_{average}}

    The ratio of largest to smallest is  \n
    .. math:: ratio = \\frac{Imax}{Imin}

    The semiaxes a,b and c are those of an ellipsoid \n
    .. math:: semiaxis_a = \\sqrt{ \\frac{5}{2M} (I_{max}+I_{mid}-I_{min}) }
    .. math:: semiaxis_b = \\sqrt{ \\frac{5}{2M} (I_{max}+I_{min}-I_{mid}) }
    .. math:: semiaxis_c = \\sqrt{ \\frac{5}{2M} (I_{mid}+I_{min}-I_{max}) }

    Where:\n
        - M is the total mass of all the selected atoms
        - :math:`I_{min}` , :math:`I_{mid}` and :math:`I_{max}` are respectively the smallest, middle and biggest inertia moment values


    **Output:** \n
    #. moment_of_inertia_xx: the moment of inertia in x direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_xy: the moment of inertia in y direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_xz: the moment of inertia in z direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_yy: the moment of inertia in y direction acting on the surface element with its vector normal in y direction
    #. moment_of_inertia_yz: the moment of inertia in z direction acting on the surface element with its vector normal in y direction
    #. moment_of_inertia_zz: the moment of inertia in z direction acting on the surface element with its vector normal in z direction
    #. semiaxis_a: ellipse biggest axis
    #. semiaxis_b: ellipse middle axis
    #. semiaxis_c: ellipse smallest axis
    #. ratio_of_largest_to_smallest
    #. eccentricity
    #. radius_of_gyration


    **Usage:** \n
    This analysis can be used to study macro-molecular geometry and sphericity .
    It was originally conceived to calculate the ellipticity of micelles.

    **Acknowledgement and publication:**\n
    AOUN Bachir, PELLEGRINI Eric

    """

    label = "Eccentricity"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["center_of_mass"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(log_filename)

        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        npoints = np.zeros((self.configuration["frames"]["number"]), dtype=np.float64)

        for axis in ["xx", "xy", "xz", "yy", "yz", "zz"]:
            self._outputData.add(
                "moment_of_inertia_{}".format(axis),
                "LineOutputVariable",
                npoints,
                axis="time",
                units="uma nm2",
            )
        for axis in ["a", "b", "c"]:
            self._outputData.add(
                "semiaxis_{}".format(axis),
                "LineOutputVariable",
                npoints,
                axis="time",
                units="nm",
            )

        self._outputData.add(
            "eccentricity",
            "LineOutputVariable",
            npoints,
            axis="time",
            main_result=True,
        )

        self._outputData.add(
            "ratio_of_largest_to_smallest", "LineOutputVariable", npoints, axis="time"
        )

        self._outputData.add(
            "radius_of_gyration", "LineOutputVariable", npoints, axis="time"
        )

        self._indexes = self.configuration["atom_selection"].get_indexes()

        self._comIndexes = self.configuration["center_of_mass"]["flatten_indexes"]

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

        self._selectionMasses = [
            m
            for masses in self._configuration["atom_selection"]["masses"]
            for m in masses
        ]
        self._selectionTotalMass = np.sum(self._selectionMasses)

        self._comMasses = [
            ATOMS_DATABASE.get_atom_property(self._atoms[idx].symbol, "atomic_weight")
            for idx in self._comIndexes
        ]

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. moment_of_inertia_xx (np.array)
            #. moment_of_inertia_xy (np.array)
            #. moment_of_inertia_xz (np.array)
            #. moment_of_inertia_yy (np.array)
            #. moment_of_inertia_yz (np.array)
            #. moment_of_inertia_zz (np.array)
            #. radius_of_gyration (np.array)
        """
        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.continuous_configuration()

        series = conf["coordinates"]

        com = center_of_mass(series[self._comIndexes, :], masses=self._comMasses)

        # calculate the inertia moments and the radius of gyration
        xx = xy = xz = yy = yz = zz = 0
        for name, idxs in list(self._indexes.items()):
            atomsCoordinates = series[idxs, :]
            difference = atomsCoordinates - com

            w = ATOMS_DATABASE.get_atom_property(
                name, self.configuration["weights"]["property"]
            )

            xx += np.add.reduce(
                w
                * (
                    difference[:, 1] * difference[:, 1]
                    + difference[:, 2] * difference[:, 2]
                )
            )
            xy -= np.add.reduce(w * (difference[:, 0] * difference[:, 1]))
            xz -= np.add.reduce(w * (difference[:, 0] * difference[:, 2]))

            yy += np.add.reduce(
                w
                * (
                    difference[:, 0] * difference[:, 0]
                    + difference[:, 2] * difference[:, 2]
                )
            )
            yz -= np.add.reduce(w * (difference[:, 1] * difference[:, 2]))

            zz += np.add.reduce(
                w
                * (
                    difference[:, 0] * difference[:, 0]
                    + difference[:, 1] * difference[:, 1]
                )
            )

        rog = np.sum((series - com) ** 2)

        return index, (xx, xy, xz, yy, yz, zz, rog)

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        Imin = min(x[0], x[3], x[5])
        Imax = max(x[0], x[3], x[5])
        Imid = [x[0], x[3], x[5]]
        Imid.pop(Imid.index(Imin))
        Imid.pop(Imid.index(Imax))
        Imid = Imid[0]

        average = (x[0] + x[3] + x[5]) / 3

        # moment of inertia
        self._outputData["moment_of_inertia_xx"][index] = x[0]
        self._outputData["moment_of_inertia_xy"][index] = x[1]
        self._outputData["moment_of_inertia_xz"][index] = x[2]
        self._outputData["moment_of_inertia_yy"][index] = x[3]
        self._outputData["moment_of_inertia_yz"][index] = x[4]
        self._outputData["moment_of_inertia_zz"][index] = x[5]

        # eccentricity = 0 for spherical objects
        self._outputData["eccentricity"][index] = 1 - Imin / average

        # ratio_of_largest_to_smallest = 1 for spherical objects
        self._outputData["ratio_of_largest_to_smallest"][index] = Imax / Imin

        # semiaxis
        self._outputData["semiaxis_a"][index] = np.sqrt(
            5.0 / (2.0 * self._selectionTotalMass) * (Imax + Imid - Imin)
        )
        self._outputData["semiaxis_b"][index] = np.sqrt(
            5.0 / (2.0 * self._selectionTotalMass) * (Imax + Imin - Imid)
        )
        self._outputData["semiaxis_c"][index] = np.sqrt(
            5.0 / (2.0 * self._selectionTotalMass) * (Imid + Imin - Imax)
        )

        # radius_of_gyration is a measure of the distribution of the mass
        # of atomic groups or molecules that constitute the aqueous core
        # relative to its center of mass
        self._outputData["radius_of_gyration"][index] = np.sqrt(
            x[6] / self.configuration["atom_selection"]["selection_length"]
        )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()

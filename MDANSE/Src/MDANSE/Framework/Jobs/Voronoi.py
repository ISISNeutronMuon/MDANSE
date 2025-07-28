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

import collections
import math

import numpy as np
from scipy.spatial import Delaunay as scipyDelaunay
from scipy.spatial import Voronoi as scipyVoronoi

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Configuration import padded_coordinates


def no_exc_min(numbers: list[float]):
    try:
        return min(numbers)
    except ValueError:
        return -1
    except TypeError:
        return -2


class VoronoiError(Exception):
    pass


class Voronoi(IJob):
    """Performs the Voronoi analysis of available volume per atom.

    Computes the volume of each Voronoi cell and corresponding 'neighbourhood'
    statistics for 3d systems. Vornoi diagram and Delaunay tesselation are
    used as implemented in scipy.spatial module. Replicas of atoms from
    the simulation box will be included in the calculation within
    a finite distance from the box wall (given in nm).

    Voronoi analysis is another commonly-used, complementary method for
    characterising the local structure of a system.

    **Acknowledgement:**
    Gael Goret, PELLEGRINI Eric

    """

    label = "Voronoi"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 5, 1)},
    )
    settings["pbc"] = (
        "BooleanConfigurator",
        {"label": "apply periodic_boundary_condition", "default": True},
    )
    settings["pbc_border_size"] = ("FloatConfigurator", {"mini": 0.0, "default": 0.2})
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "voronoi/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        # Will store mean volume for voronoi regions.
        self.mean_volume = np.zeros(self.numberOfSteps)

        self.nb_init_pts = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        # Will store neighbourhood histogram for voronoi regions.
        self.neighbourhood_hist = {}

        first_conf = self.trajectory.configuration()

        try:
            cell = first_conf.unit_cell.direct
            self.cell_param = np.array(
                [cell[0, 0], cell[1, 1], cell[2, 2]], dtype=np.float64
            )
        except Exception:
            raise VoronoiError(
                "Voronoi analysis cannot be computed if simulation box is not defined. "
                "You can add a box using TrajectoryEditor."
            )

        self.dim = 3

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.trajectory.configuration(frameIndex)
        unit_cell = conf._unit_cell

        if self.configuration["pbc"]["value"]:
            coords, _ = padded_coordinates(
                conf["coordinates"],
                unit_cell,
                self.configuration["pbc_border_size"]["value"],
            )
        else:
            coords = conf["coordinates"]

        # Computing Voronoi Diagram
        Voronoi = scipyVoronoi(coords)
        vertices_coords = Voronoi.vertices  # Option qhull v p

        # Extracting valid Voronoi regions
        points_ids = Voronoi.regions  # Option qhull v FN
        valid_regions_points_ids = []
        valid_region_id = []
        region_id = -1
        for p in Voronoi.point_region:
            region_id += 1
            id_list = points_ids[p]
            if no_exc_min(id_list) >= 0:
                valid_regions_points_ids.append(id_list)
                valid_region_id.append(region_id)

        valid_regions = {}
        for i in range(len(valid_region_id)):
            vrid = valid_region_id[i]
            valid_regions[vrid] = valid_regions_points_ids[i]

        # Extracting ridges of the valid Voronoi regions
        input_sites = Voronoi.ridge_points  # Option qhull v Fv (part of)
        self.max_region_id = input_sites.max()

        # Calculating neighbourhood
        neighbourhood = np.zeros((self.max_region_id + 1), dtype=np.int32)
        for s in input_sites.ravel():
            neighbourhood[s] += 1

        # Summing into neighbourhood histogram (for valid regions only)
        for i in range(len(neighbourhood)):
            v = neighbourhood[i]
            if i in valid_region_id:
                if v not in self.neighbourhood_hist.keys():
                    self.neighbourhood_hist[v] = 1
                else:
                    self.neighbourhood_hist[v] += 1

        # Delaunay Tesselation of each valid voronoi region
        delaunay_regions_for_each_valid_voronoi_region = {}
        for vrid, ids in list(valid_regions.items()):
            if vrid >= self.nb_init_pts:
                continue
            if len(ids) == 3:
                delaunay_regions_for_each_valid_voronoi_region[vrid] = [ids]
                continue
            lut = np.array(ids)
            Delaunay = scipyDelaunay(vertices_coords[ids])
            delaunay_regions_for_each_valid_voronoi_region[vrid] = [
                lut[dv] for dv in Delaunay.simplices
            ]

        # Volume Computation
        global_volumes = {}
        for vrid, regions in list(
            delaunay_regions_for_each_valid_voronoi_region.items()
        ):
            regions_volumes = []
            for vidx in regions:
                coords = vertices_coords[vidx]
                delta = coords[1:, :] - coords[0, :]
                vidx_volume = np.abs(np.linalg.det(delta)) / math.factorial(self.dim)
                regions_volumes.append(vidx_volume)
            global_volumes[vrid] = sum(regions_volumes)

        # Mean volume of Voronoi regions
        mean = np.array(list(global_volumes.values())).mean()
        self.mean_volume[index] = mean

        return index, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x: the output of run_step method.
        @type x: no specific type.
        """
        pass

    def finalize(self):
        """
        Finalize the job.
        """
        max_nb_neighbour = max(self.neighbourhood_hist.keys())
        self.neighbourhood = np.zeros((max_nb_neighbour + 1), dtype=np.int32)
        for k, v in self.neighbourhood_hist.items():
            self.neighbourhood[k] = v

        self._outputData.add(
            "voronoi/mean_volume",
            "LineOutputVariable",
            self.mean_volume,
            units="nm3",
            main_result=True,
        )

        self._outputData.add(
            "voronoi/neighbourhood_histogram",
            "LineOutputVariable",
            self.neighbourhood,
            units="au",
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()

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

import numpy as np

from MDANSE.Framework.Configurators.FloatConfigurator import FloatConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory

AXIS_INDEX = {"a": 0, "b": 1, "c": 2}


class GridStepConfigurator(FloatConfigurator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["grid"] = []
        self.prediction_key = "grid"
        self.prediction_unit = "nm"

    def configure(self, value):
        super().configure(value)

        trajectory: Trajectory = self.configurable[self.dependencies["trajectory"]][
            "instance"
        ]
        unit_cell = trajectory.unit_cell(0)._unit_cell
        if unit_cell is None:
            axes = trajectory.max_span
        else:
            axes = np.linalg.norm(unit_cell, axis=0)
        if "axis" in self.dependencies:
            axis = self.configurable[self.dependencies["axis"]]["value"]
            axis_length = axes[AXIS_INDEX[axis]]
            self["grid"] = np.arange(0.0, axis_length, self["value"])
            return
        self["grid"] = [np.arange(0, axes[index], self["value"]) for index in range(3)]

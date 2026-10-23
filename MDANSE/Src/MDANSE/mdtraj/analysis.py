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

from collections import Counter
from collections.abc import Callable
from inspect import getfullargspec
from operator import itemgetter
from typing import TYPE_CHECKING, Any

import numpy as np

from MDANSE.Framework.AtomGrouping.grouping import pair_labels

if TYPE_CHECKING:
    import numpy.typing as npt

    from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
    from MDANSE.MolecularDynamics.Trajectory import Trajectory


def mdtraj_initial_params(
    mdtraj_analysis: Callable,
) -> tuple[list[str], list[tuple[str, Any]]]:
    """Return input arguments accepted by a function.

    Designed to find all the keyword arguments of an MDTraj analysis run
    and their default values.

    Parameters
    ----------
    mdtraj_analysis : Callable
        A function run on an MDTraj trajectory.

    Returns
    -------
    tuple[list[str], list[tuple[str, Any]]]
        List of arguments and dictionary of keyword arguments with default values.
    """
    full_arg_spec = getfullargspec(mdtraj_analysis)
    param_names = full_arg_spec.args
    default_vals = list(full_arg_spec.defaults)
    pars_with_vals = []
    while default_vals:
        pars_with_vals.append((param_names.pop(), default_vals.pop()))
    return param_names, pars_with_vals[::-1]

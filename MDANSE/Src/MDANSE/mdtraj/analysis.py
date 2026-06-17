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

from collections.abc import Callable
from inspect import getfullargspec


def mdtraj_initial_params(mdtraj_analysis: Callable):
    full_arg_spec = getfullargspec(mdtraj_analysis)
    param_names = full_arg_spec.args
    default_vals = full_arg_spec.defaults
    pars_with_vals = []
    while default_vals:
        pars_with_vals.append((param_names.pop(), default_vals.pop()))
    return param_names, pars_with_vals[::-1]

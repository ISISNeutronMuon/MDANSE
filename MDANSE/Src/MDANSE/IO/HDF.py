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
import numpy as np

import h5py


def find_numeric_variables(variables, group):
    """This method retrieves all the numeric variables stored in the HDF file.

    This is a recursive method.
    """

    for var_key, var in group.items():
        if isinstance(var, h5py.Group):
            find_numeric_variables(variables, var)
        else:
            if var.parent.name == "/":
                path = "/{}".format(var_key)
            else:
                path = "{}/{}".format(var.parent.name, var_key)

            if not np.issubdtype(var.dtype, np.number):
                continue

            variables.append(path)

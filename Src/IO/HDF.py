import numpy as np

import h5py

def find_numeric_variables(variables, group):
    """This method retrieves all the numeric variables stored in the NetCDF file.

    This is a recursive method.
    """

    for var_key, var in group.items():

        if isinstance(var,h5py.Group):
            find_numeric_variables(variables,var)
        else:

            if var.parent.name == '/':
                path = '/{}'.format(var_key)
            else:
                path = '{}/{}'.format(var.parent.name, var_key)

            # Non numeric variables are not supported by the plotter
            if not np.issubdtype(var.dtype, np.number):
                continue

            variables.append(path)

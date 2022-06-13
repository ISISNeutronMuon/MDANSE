import numpy as np

def find_numeric_variables(variables, group):
    """This method retrieves all the numeric variables stored in the NetCDF file.

    This is a recursive method.
    """

    for var_key, var in group.variables.items():
        if group.path == '/':
            path = '/{}'.format(var_key)
        else:
            path = '{}/{}'.format(group.path, var_key)

        # Non numeric variables are not supported by the plotter
        if not np.issubdtype(var.dtype, np.number):
            continue

        variables.append(path)

    for _, sub_group in group.groups.items():
        find_numeric_variables(variables, sub_group)

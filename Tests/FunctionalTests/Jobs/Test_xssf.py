#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['atom_selection'] = 'all'
parameters['frames'] = (0, 10, 1)
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['q_values'] = (0, 10, 1)
parameters['r_values'] = (0, 10, 1)
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
parameters['transmutated_atoms'] = None

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['xssf'](status=False)
job.run(parameters)
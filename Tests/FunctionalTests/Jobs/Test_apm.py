#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['axis'] = ['a', 'b']
parameters['frames'] = (0, 10, 1)
parameters['name'] = 'DMPC'
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/dmpc_in_periodic_universe.nc'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['apm'](status=False)
job.run(parameters)
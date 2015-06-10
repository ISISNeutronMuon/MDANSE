#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['axis'] = 'c'
parameters['frames'] = (0, 10, 1)
parameters['lower_leaflet'] = 'DMPC'
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/dmpc_in_periodic_universe.nc'
parameters['upper_leaflet'] = 'DMPC'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['rmt'](status=False)
job.run(parameters)
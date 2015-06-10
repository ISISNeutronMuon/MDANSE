#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['axis_selection'] = {'endpoint1': ('OW',), 'endpoint2': ('HW',), 'molecule': 'Water'}
parameters['frames'] = (0, 10, 1)
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['per_axis'] = False
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['ac'](status=False)
job.run(parameters)
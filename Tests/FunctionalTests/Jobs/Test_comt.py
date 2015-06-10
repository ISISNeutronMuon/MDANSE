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
parameters['frames'] = (0, 1, 1)
parameters['grouping_level'] = 'atom'
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['comt'](status=False)
job.run(parameters)
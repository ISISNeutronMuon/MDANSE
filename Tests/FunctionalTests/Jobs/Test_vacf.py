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
parameters['atom_transmutation'] = None
parameters['frames'] = (0, 10, 1)
parameters['grouping_level'] = 'atom'
parameters['interpolation_order'] = 'no interpolation'
parameters['normalize'] = False
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['projection'] = None
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
parameters['weights'] = 'equal'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['vacf'](status=False)
job.run(parameters)
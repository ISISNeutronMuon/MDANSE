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
parameters['grouping_level'] = 'atom'
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['reference'] = 0
parameters['remove_translation'] = False
parameters['running_mode'] = ('monoprocessor', 1)
parameters['stepwise'] = True
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['rbt'](status=False)
job.run(parameters)
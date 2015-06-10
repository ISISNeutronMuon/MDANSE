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
parameters['projection'] = None
parameters['q_vectors'] = ('spherical_lattice', {'width': 0.1, 'n_vectors': 50, 'shells': (0, 5, 0.1)})
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
parameters['transmutated_atoms'] = None
parameters['weights'] = 'b_incoherent'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['eisf'](status=False)
job.run(parameters)
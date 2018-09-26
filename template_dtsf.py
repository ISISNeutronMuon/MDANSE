#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
########################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['atom_selection'] = 'all'
parameters['atom_transmutation'] = None
parameters['frames'] = (0, 10, 1)
parameters['instrument_resolution'] = ('gaussian', {'mu': 0.0, 'sigma': 10.0})
parameters['output_files'] = ('output', ['netcdf'])
parameters['q_vectors'] = ('spherical_lattice', {'width': 0.1, 'n_vectors': 50, 'shells': (0.1, 5, 0.1)})
parameters['running_mode'] = ('monoprocessor', 1)
parameters['trajectory'] = '/home/pellegrini/git/mdanse/Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
parameters['weights'] = 'b_coherent'

################################################################
# Setup and run the analysis                                   #
################################################################

dtsf = REGISTRY['job']['dtsf']()
dtsf.run(parameters,status=True)

#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['nb_frame'] = (0, 2, 1)
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['pdb_file'] = '../../../Data/Trajectories/PDB/2f58_nma.pdb'
parameters['time_step'] = 1.0

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['pdb'](status=False)
job.run(parameters)
#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['atom_aliases'] = {}
parameters['field_file'] = '../../../Data/Trajectories/DL_Poly/FIELD_cumen'
parameters['history_file'] = '../../../Data/Trajectories/DL_Poly/HISTORY_cumen'
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['version'] = '2'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['dl_poly'](status=False)
job.run(parameters)
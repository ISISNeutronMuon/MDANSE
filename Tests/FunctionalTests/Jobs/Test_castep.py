#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['castep_file'] = '../../../Data/Trajectories/CASTEP/PBAnew.md'
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['castep'](status=False)
job.run(parameters)
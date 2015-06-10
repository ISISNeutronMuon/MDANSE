#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['his_file'] = '../../../Data/Trajectories/Discover/sushi.his'
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['xtd_file'] = '../../../Data/Trajectories/Discover/sushi.xtd'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['dmol'](status=False)
job.run(parameters)
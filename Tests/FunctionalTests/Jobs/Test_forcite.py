#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['trj_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.trj'
parameters['xtd_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.xtd'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['forcite'](status=False)
job.run(parameters)
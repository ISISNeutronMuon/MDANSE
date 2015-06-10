#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['gt_file'] = '../../../Data/Trajectories/Generic/test.gtf'
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['generic'](status=False)
job.run(parameters)
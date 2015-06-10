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
parameters['time_step'] = 1.0
parameters['xdatcar_file'] = '../../../Data/Trajectories/VASP/XDATCAR_version5'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['vasp'](status=False)
job.run(parameters)
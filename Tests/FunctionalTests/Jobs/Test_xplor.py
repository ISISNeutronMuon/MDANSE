#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['dcd_file'] = '../../../Data/Trajectories/CHARMM/2vb1.dcd'
parameters['fold'] = False
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['pdb_file'] = '../../../Data/Trajectories/CHARMM/2vb1.pdb'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['xplor'](status=False)
job.run(parameters)
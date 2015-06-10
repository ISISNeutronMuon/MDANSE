#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['config_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.config'
parameters['n_steps'] = 1
parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
parameters['time_step'] = 1.0
parameters['trajectory_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.lammps'

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['lammps'](status=False)
job.run(parameters)
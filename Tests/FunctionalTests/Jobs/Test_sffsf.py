#!/usr/bin/python

########################################################
# This is an automatically generated MDANSE run script #
#######################################################

from MDANSE import REGISTRY

################################################################
# Job parameters                                               #
################################################################

parameters = {}
parameters['instrument_resolution'] = ('gaussian', {'mu': 0.0, 'sigma': 10.0})
parameters['netcdf_input_file'] = '../../../Data/NetCDF/disf_prot.nc'
parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])

################################################################
# Setup and run the analysis                                   #
################################################################

job = REGISTRY['job']['sffsf'](status=False)
job.run(parameters)
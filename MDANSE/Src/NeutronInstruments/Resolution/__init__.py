# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Resolution/__init__.py
# @brief     Implements __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

"""The greatest challenge so far in the realistic neutron instrument
implementation, the resolution calculation, will be different for
different experiment methods. Knowledge of instrument parameters
will be required.

Typically, for an Inelastic Neutron Scattering instrument, the
resolution will depend on the source-sample and sample-detector
distances, the chopper speeds, and the Ei/Ef ratio."""

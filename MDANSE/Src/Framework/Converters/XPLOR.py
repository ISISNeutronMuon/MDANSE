# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/XPLOR.py
# @brief     Implements module/class/test XPLOR
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from MDANSE.Framework.Converters.DCD import DCD


class XPLOR(DCD):
    """
    Converts an Xplor trajectory to a HDF trajectory.
    """

    label = "XPLOR"

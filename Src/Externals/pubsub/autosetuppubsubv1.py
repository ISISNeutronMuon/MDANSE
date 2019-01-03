# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/autosetuppubsubv1.py
# @brief     Implements module/class/test autosetuppubsubv1
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

'''
If this module is named autosetuppubsubv1, and it is in the pubsub
package's folder, it will cause pubsub to default to "version 1" (v1)
of the API when pub is imported. The v1 API was the version originally
developed as part of wxPython's wx.lib library.

If this module is named anything else (such as prefixed with an
underscore) it will not be found by pubsub: the most recent pubsub
API will be loaded upon import of the *pub* module.
'''
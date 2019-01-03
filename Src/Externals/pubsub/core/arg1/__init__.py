# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/arg1/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
This is not really a package init file, it is only here to simplify the
packaging and installation of pubsub.core's protocol-specific subfolders
by setuptools.  The python modules in this folder are automatically made
part of pubsub.core via pubsub.core's __path__. Hence, this should not
be imported directly, it is part of pubsub.core when the messaging
protocol is "arg1" (and not usable otherwise).

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.

"""


msg = 'Should not import this directly, used by pubsub.core if applicable'
raise RuntimeError(msg)
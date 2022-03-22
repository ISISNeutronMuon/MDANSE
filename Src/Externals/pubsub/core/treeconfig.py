# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/treeconfig.py
# @brief     Implements module/class/test treeconfig
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""

from .notificationmgr import NotificationMgr


class TreeConfig:
    """
    Each topic tree has its own topic manager and configuration,
    such as notification and exception handling.
    """

    def __init__(self, notificationHandler=None, listenerExcHandler=None):
        self.notificationMgr = NotificationMgr(notificationHandler)
        self.listenerExcHandler = listenerExcHandler
        self.raiseOnTopicUnspecified = False



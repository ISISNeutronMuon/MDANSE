# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/policies.py
# @brief     Implements module/class/test policies
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
Aggregates policies for pubsub. Mainly, related to messaging protocol. 

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""

msgProtocolTransStage = None

msgDataProtocol    = 'kwargs'
msgDataArgName     = None
senderKwargNameAny = False


def setMsgDataArgName(stage, listenerArgName, senderArgNameAny=False):
    global senderKwargNameAny
    global msgDataArgName
    global msgProtocolTransStage
    senderKwargNameAny = senderArgNameAny
    msgDataArgName = listenerArgName
    msgProtocolTransStage = stage
    #print `policies.msgProtocolTransStage`, `policies.msgDataProtocol`, \
    #      `policies.senderKwargNameAny`, `policies.msgDataArgName`
    #print 'override "arg1" protocol arg name:', argName

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/arg1/publisher.py
# @brief     Implements module/class/test publisher
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
Mixin for publishing messages to a topic's listeners. This will be
mixed into topicobj.Topic so that a user can use a Topic object to
send a message to the topic's listeners via a publish() method.

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""


from .publisherbase import PublisherBase


class Publisher(PublisherBase):
    """
    Publisher that allows old-style Message.data messages to be sent
    to listeners. Listeners take one arg (required, unless there is an
    *arg), but can have kwargs (since they have default values).
    """

    def sendMessage(self, topicName, data=None):
        """Send message of type topicName to all subscribed listeners,
        with message data. If topicName is a subtopic, listeners
        of topics more general will also get the message.

        Note that any listener that lets a raised exception escape will
        interrupt the send operation, unless an exception handler was
        specified via pub.setListenerExcHandler().
        """
        topicMgr = self.getTopicMgr()
        topicObj = topicMgr.getOrCreateTopic(topicName)

        # don't care if topic not final: topicObj.getListeners()
        # will return nothing if not final but notification will still work

        topicObj.publish(data)

    def getMsgProtocol(self):
        return 'arg1'


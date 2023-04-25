# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/kwargs/publishermixin.py
# @brief     Implements module/class/test publishermixin
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""


class PublisherMixin:
    """
    Mixin for publishing messages to a topic's listeners. This will be
    mixed into topicobj.Topic so that a user can use a Topic object to
    send a message to the topic's listeners via a publish() method.

    Note that it is important that the PublisherMixin NOT modify any
    state data during message sending, because in principle it could
    happen that a listener causes another message of same topic to be
    sent (presumably, the listener has a way of preventing infinite
    loop).
    """

    def __init__(self):
        pass

    def publish(self, **msgKwargs):
        self._publish(msgKwargs)

    ############## IMPLEMENTATION ###############
    
    class IterState:
        def __init__(self, msgKwargs):
            self.filteredArgs = msgKwargs
            self.argsChecked = False

        def checkMsgArgs(self, spec):
            spec.check(self.filteredArgs)
            self.argsChecked = True

        def filterMsgArgs(self, topicObj):
            if self.argsChecked:
                self.filteredArgs = topicObj.filterMsgArgs(self.filteredArgs)
            else:
                self.filteredArgs = topicObj.filterMsgArgs(self.filteredArgs, True)
                self.argsChecked = True

    def _mix_prePublish(self, msgKwargs, topicObj=None, iterState=None):
        if iterState is None:
            # do a first check that all args are there, costly so only do once
            iterState = self.IterState(msgKwargs)
            if self.hasMDS():
                iterState.checkMsgArgs( self._getListenerSpec() )
            else:
                assert not self.hasListeners()

        else:
            iterState.filterMsgArgs(topicObj)

        assert iterState is not None
        return iterState

    def _mix_callListener(self, listener, msgKwargs, iterState):
        """Send the message for given topic with data in msgKwargs.
        This sends message to listeners of parent topics as well.
        Note that at each level, msgKwargs is filtered so only those
        args that are defined for the topic are sent to listeners. """
        listener(iterState.filteredArgs, self, msgKwargs)


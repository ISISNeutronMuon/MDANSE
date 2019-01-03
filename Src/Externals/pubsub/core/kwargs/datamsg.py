# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/kwargs/datamsg.py
# @brief     Implements module/class/test datamsg
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""

class Message:
    """
    A simple container object for the two components of a message in the 
    arg1 messaging protocol: the 
    topic and the user data. Each listener called by sendMessage(topic, data)
    gets an instance of Message. The given 'data' is accessed
    via Message.data, while the topic name is available in Message.topic::
    
        def listener(msg):
            print "data is ", msg.data
            print "topic name is ", msg.topic
            print msg
            
    The example also shows (last line) how a message is convertible to a string.
    """
    def __init__(self, topic, data):
        self.topic = topic
        self.data  = data

    def __str__(self):
        return '[Topic: '+repr(self.topic)+',  Data: '+repr(self.data)+']'


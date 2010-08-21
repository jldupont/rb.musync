"""
    Message Bridge
    
    Performs "bridging" of messages between the shared Bus (mbus)
    living on the main-thread and the other threads hanging off
    the "mswitch"

    Why do we have to go through this trouble?
    ------------------------------------------
    
    I wanted to use "agents" interacting with RB but those couldn't
    be thread based as RB wasn't designed to work with those (at least
    that's the way I believe the situation to be).
 

    @author: jldupont
    @date: Jun 3, 2010
"""
from Queue import Queue

from musync.system.mbus import Bus
from musync.system.base import mswitch, custom_dispatch


class BridgeAgent(object):
    
    NAME="__bridge__"
    
    def __init__(self):
        
        self.iq=Queue()  #normal queue
        self.ipq=Queue() #high priority queue
        
        Bus.subscribe(self.NAME, "*", self.h_msg)
        
    def _dispatcher(self, *pargs):
        handled=Bus.publish(self.NAME, *pargs)
        return handled
        
    def h_msg(self, mtype, *pa):        
        #if mtype!="tick":
        #    print "to mswitch: mtype(%s) pa:%s" % (mtype, pa)
        mswitch.publish(self.NAME, mtype, *pa)

        if mtype=="tick":
            custom_dispatch(self.NAME, 
                            self.iq, self.ipq, 
                            self._dispatcher)


_=BridgeAgent()
mswitch.subscribe(_.iq, _.ipq)

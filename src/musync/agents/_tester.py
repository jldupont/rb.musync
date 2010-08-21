"""
    
        
    Created on 2010-08-20
    @author: jldupont
"""
from sync_ratings.system.base import AgentThreadedWithEvents

class TesterAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         ("sec", 1, "t_sec")
        ,("min", 1, "t_min")
    ]
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        
    def t_sec(self, *_):
        print "tsec!"
    
    def t_min(self, *_):
        pass
        
    def h_entry_changed(self, entry):
        print entry
        
        
_=TesterAgent()
_.start()

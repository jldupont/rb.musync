"""
    Just for testing...
        
    Created on 2010-08-20
    @author: jldupont
"""
from musync.system.base import AgentThreadedWithEvents

class TesterAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         ("sec", 1, "t_sec")
        ,("min", 1, "t_min")
    ]
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        
    def t_sec(self, *_):
        pass
    
    def t_min(self, *_):
        pass
        
    def h_entry_changed(self, entry):
        pass
        #print entry
        
        
_=TesterAgent()
_.start()

"""
    Monitor Agent
    
    Messages Processed:
    ===================
    
    Messages Emitted:
    =================
    - "rb_load_completed"
    
        
    Created on 2010-08-21
    @author: jldupont
"""
__all__=[""]
from musync.system.base import AgentThreadedWithEvents

class MonitorAgent(AgentThreadedWithEvents):

    TIMERS_SPEC=[    
         ("sec",  5, "t_sec")
        ,("min",  1, "t_min")
    ]
    
    def __init__(self):
        AgentThreadedWithEvents.__init__(self)
        self.start_phase=True
        
    def t_sec(self, *_):
        pass
            
    def t_min(self, *_):
        pass
       
    def h_entry_changed(self, _entry_id, _entry, _changes):
        pass
        
    def h_load_complete(self, *_):
        """ Comes way too early to my taste
            Appears to be fired when the application is loaded
            and definitely not when the database is ready
        """
        
    def h_rb_load_completed(self, song_entries_id_list):
        self.start_phase=False
        
        
_=MonitorAgent()
_.start()

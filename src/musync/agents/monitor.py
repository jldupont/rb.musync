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
    
    def __init__(self, debug=False):
        AgentThreadedWithEvents.__init__(self, debug=debug)
        self.start_phase=True
        
    def t_sec(self, *_):
        print "monitor.t_sec"
            
    def t_min(self, *_):
        pass
       
    def hs_entry_changed(self):
        pass
        
    def hs_load_complete(self, *p):
        """ Comes way too early to my taste
            Appears to be fired when the application is loaded
            and definitely not when the database is ready
        """
        print "####### hs_load_complete:"+str(p)

    def h_load_complete(self, *p):
        """ Comes way too early to my taste
            Appears to be fired when the application is loaded
            and definitely not when the database is ready
        """
        print "####### h_load_complete ############"+ str(p)
        
    def hs_rb_load_completed(self):
        self.start_phase=False
        print "####### hs_rb_load_completed:"
        
_=MonitorAgent(True)
_.start()

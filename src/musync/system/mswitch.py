"""
    Message Switch
    
    * high/low priority queues
    * message dispatching based on 'interest' communicated by Agent
    * message bursting controlled
    
    @author: jldupont
    @date: May 17, 2010
    @revised: June 18, 2010
    @revised: August 22, 2010 : filtered-out "send to self" case    
"""

from threading import Thread
from Queue import Queue, Empty

__all__=["publish", "subscribe", "observe_mode"]
OSBSERVE_FILTER_OUT=["__tick__", "log", "llog"]
            
observe_mode=False

class BasicSwitch(Thread):
    """
    Simple message switch
    
    Really just broadcasts the received
    message to all 'clients' in 'split horizon'
    i.e. not sending back to originator
    """
    
    LOW_PRIORITY_BURST_SIZE=5
    
    def __init__(self):
        Thread.__init__(self)
        
        #self.rmap={} ## debug only
        
        self.imap={}
        self.clients=[]
        self.iq=Queue()
        
        ## system queue - high priority
        self.isq=Queue()
    
    def run(self):
        """
        Main loop
        """
        quit=False
        while not quit:
            while True:
                
                ### There should be only a low volume/frequency
                ### of 'high priority' system messages.
                ### We'll get back through here soon enough i.e.
                ###  after the other queue's timeout / 1 msg processed
                try:
                    envelope=self.isq.get(block=False)
                    orig, mtype, payload=envelope
                    
                    if mtype=="__interest__":
                        self.do_interest(payload)
                    else:
                        self.do_pub(orig, mtype, payload)
                    ## We needed to give a chance to
                    ## all threads to exit before
                    ## committing "hara-kiri"
                    if mtype=="__quit__":
                        quit=True

                    ## high priority messages are processed until
                    ## exhaustion
                    continue
                except Empty:
                    break
    
            burst=self.LOW_PRIORITY_BURST_SIZE
            
            while True:
                try:            
                    ## normal priority queue            
                    envelope=self.iq.get(block=True, timeout=0.1)
                    orig, mtype, payload=envelope
                    if mtype=="__sub__":
                        sorig, q, sq=payload
                        self.do_sub(sorig, q, sq)
                    else:
                        self.do_pub(orig, mtype, payload)

                    if mtype=="__quit__":
                        quit=True
                                            
                    #if mtype != "tick":
                    #    print "mswitch: mtype(%s)" % mtype
                    
                    ## Only processed a "burst" of low priority messages
                    ##  before checking the "high priority" queue
                    burst -= 1
                    if burst==0:
                        break
                except Empty:
                    break
        
        print "mswitch - shutdown"
        
    def do_interest(self, payload):
        """
        Add a 'subscriber' for 'mtype'
        """
        _orig, msg, _pargs, _kargs = payload
        mtype, interest, q = msg
        self.imap[(q, mtype)]=interest
               
                
    def do_sub(self, orig, q, sq):
        """
        Performs subscription
        """
        self.clients.append((orig, q, sq))
        
    def do_pub(self, orig, mtype, payload):
        """
        Performs message distribution
        """
        #print "do_pub: mtype: %s  payload: %s" % (mtype, payload)
        for sorig, q, sq in self.clients:
            
            ## don't send to self!
            if sorig==orig:
                continue
            
            interest=self.imap.get((q, mtype), None)
            
            """
            if interest==False:
                reported=self.rmap.get((q, mtype), None)
                if reported is None:
                    print "agent(%s) not interested mtype(%s)" % (str(q), mtype)
                    self.rmap[(q, mtype)]=True
            """
                
            ### Agent notified interest OR not sure yet            
            if interest==True or interest==None:

                if observe_mode:
                    if mtype not in OSBSERVE_FILTER_OUT:
                        print "<<< do_pub: interest(%s) mtype(%s) q(%s) sq(%s)" % (interest, mtype, q, sq)
                
                if mtype.startswith("__"):
                    sq.put((sorig, mtype, payload), block=False)
                else:
                    q.put((sorig, mtype, payload), block=False)
            #if mtype!="tick":                    
            #    print ">>> do_pub: mtype(%s) q(%s) sq(%s)" % (mtype, q, sq)
    


## ===============================================================  
## =============================================================== API functions
## =============================================================== 
        

def publish(orig, msgType, msg=None, *pargs, **kargs):
    """
    Publish a 'message' of type 'msgType' to
    all registered 'clients'
    """
    if msgType.startswith("__"):
        _switch.isq.put((orig, msgType, (orig, msg, pargs, kargs)), block=False)
    else:
        _switch.iq.put((orig, msgType, (orig, msg, pargs, kargs)), block=False)
    
    
def subscribe(orig, q, sq, _msgType=None):
    """
    Subscribe a 'client' to all the switch messages
     
    @param q: client's input queue
    """
    _switch.iq.put((orig, "__sub__", (orig, q, sq)))
    



_switch=BasicSwitch()
_switch.start()

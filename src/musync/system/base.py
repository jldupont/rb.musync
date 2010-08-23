"""
    Base class for threaded Agents
    
    * high/low priority message queues
    * message bursting controlled
    * message dispatching based on Agent 'interest'
    * default handler: "h_default" , catch-all messages
    
    @author: jldupont
    @date: May 17, 2010
    @revised: June 18, 2010
    @revised: August 22, 2010 : filtered-out "send to self" case
    @revised: August 23, 2010 : added "snooping mode"    
"""

from threading import Thread
from Queue import Queue, Empty
import uuid

import mswitch

__all__=["AgentThreadedBase", "AgentThreadedWithEvents", "debug", "mdispatch"]

debug=False


def mdispatch(obj, this_source, envelope):
    """
    Dispatches a message to the target
    handler inside a class instance
    
    @return (__quit__, mtype, handled, snooping)
    
    handled:  None  --> rejected because sending to self
    handled:  True  --> message was handled by agent
    handled:  False --> message wasn't handled by agent -- no interest
    """
    orig, mtype, payload = envelope
    
    ## on snooping handlers...
    try:    pargs, kargs = payload
    except: 
        pargs=()
        kargs=()
    
    ## Avoid sending to self
    if orig == this_source:
        print "************* mdispatch: dropped: orig(%s) obj_orig(%s) mtype(%s)" % (orig, this_source, mtype)
        return (False, mtype, None, False)

    if mtype=="__quit__":
        return (True, mtype, None, False)

    handled=False
    snoopingHandler=False

    if mtype.endswith("?"):
        handlerName="hq_%s" % mtype[:-1]
        sHandlerName="hqs_%s" % mtype[:-1]
    else:
        handlerName="h_%s" % mtype
        sHandlerName="hs_%s" % mtype
        
    handler =getattr(obj, handlerName, None)
    shandler=getattr(obj, sHandlerName, None)    
    
    if handler is None:
        if shandler is not None:
            snoopingHandler=True
            handler=shandler
    
    if handler is None:
        handler=getattr(obj, "h_default", None)    
        if handler is not None:
            handler(mtype,*pargs, **kargs)
            handled=True
    else:
        handled=True
        if snoopingHandler:
            handler()
        else:
            handler(*pargs, **kargs)

    """
    if handler is None:
        if debug:
            print "! No handler for message-type: %s" % mtype
    """
    
    return (False, mtype, handled, snoopingHandler)


class AgentThreadedBase(Thread):
    """
    Base class for Agent running in a 'thread' 
    """
    
    LOW_PRIORITY_BURST_SIZE=5
    
    def __init__(self, debug=False):
        Thread.__init__(self)
        self.mmap={}
        
        self.debug=debug
        self.id = uuid.uuid1()
        self.iq = Queue()
        self.isq= Queue()
        
        self.agent_name=str(self.__class__).split(".")[-1][:-2]
        self.responsesInterest=[]
        
    def dprint(self, msg):
        if debug:
            print "+ %s: %s" % (self.__class__, msg)
        
    def pub(self, msgType, *pargs, **kargs):
        mswitch.publish(self.id, msgType, *pargs, **kargs)
        
    def run(self):
        """
        Main Loop
        """
        
        print "Agent(%s) starting" % self.agent_name
        
        ## subscribe this agent to all
        ## the messages of the switch
        mswitch.subscribe(self.id, self.iq, self.isq)
        
        quit=False
        while not quit:
            #print str(self.__class__)+ "BEGIN"
            while True:
                try:
                    envelope=self.isq.get(block=True, timeout=0.1)
                    mquit=self._process(envelope)
                    if mquit:
                        quit=True
                        break
                    continue
                except Empty:
                    break
                

            burst=self.LOW_PRIORITY_BURST_SIZE
            while True and not quit:                
                try:
                    envelope=self.iq.get(block=False)#(block=True, timeout=0.1)
                    mquit=self._process(envelope)
                    if mquit:
                        quit=True
                        break

                    burst -= 1
                    if burst == 0:
                        break
                except Empty:
                    break
        print "Agent(%s) ending" % str(self.__class__)
                
    def _process(self, envelope):
        orig, mtype, _payload = envelope
        
        #if mtype!="tick":
        #    print "base._process: mtype: " + str(mtype)
        interested=self.mmap.get(mtype, None)
        if interested==False:
            return False
        
        quit, _mtype, handled, snooping=mdispatch(self, self.id, envelope)
        if quit:
            shutdown_handler=getattr(self, "h_shutdown", None)
            if shutdown_handler is not None:
                shutdown_handler()

        ## not much more to do here...
        ## but shouldn't happen anyhow!!! #paranoia...
        if handled is None:
            return

        interestFirstTimeNoted=self.mmap.get(mtype, None)
        #if interestFirstTimeNoted is None:
        #    print "Agent(%s) mtype(%s) interested(%s) snooping(%s)" % (self.__class__, mtype, handled, snooping)
        #    print "Agent(%s) map: %s" % (self.__class__, self.mmap)

        ### signal this Agent's interest status (True/False)
        ### to the central message switch
        if interested is None:
            if mtype!="__quit__":
                if mtype not in self.responsesInterest:
                    mswitch.publish(self.id, "__interest__", self.agent_name, mtype, handled, snooping, self.iq, self.isq)
                    self.responsesInterest.append(mtype)

                    ## stop sending to self definitely
                    if handled is None:
                        handled=False
                        
                    print "+++ interest msg-orig(%s) target(%s) mtype(%s): (%s)" % (orig, self.agent_name, mtype, handled)
                    self.mmap[mtype]=handled
            
        ### This debug info is extermely low overhead... keep it.
        #if interested is None and handled:
        #    print "Agent(%s) interested(%s) snooping(%s)" % (self.__class__, mtype, snooping)
        #    print "Agent(%s) map: %s" % (self.__class__, self.mmap)

        return quit
            

class AgentThreadedWithEvents(AgentThreadedBase):
    """
    A base class for threaded Agents with timer based events support
    
    @param timers_spec: dictionary where each key represents a timer entry
    
    Timer Entry:
    ============
        [seconds_timeout, minutes_timeout, hours_timeout, days_timeout]
        
        E.g.
        ("sec", 2, callback) : will fire "callback" every 2 seconds
        ("min", 5, callback) : will fire "callback" every 5 minutes
    """
    def __init__(self, timers_spec=[], debug=False):
        AgentThreadedBase.__init__(self, debug)
        
        try:    ts=self.__class__.TIMERS_SPEC
        except: ts=[]
        
        self.timers_spec=timers_spec or ts
        self._timers={"sec":[], "min": [], "hour":[], "day": []}

        try:        
            self._processTimersSpec()
        except:
            raise RuntimeError("timers_spec misconfigured for Agent: %s" % self.__class__)
        
    def _processTimersSpec(self):
        """
        Process the timers_spec required for the Agent
        """
        for timer in self.timers_spec:
            base, interval, callback_name=timer
            entries=self._timers.get(base, [])
            entries.append((interval, callback_name))
        
        
    def h___tick__(self, _ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):
        """
        CRON like support
        """
        #print "%s: __tick__" % (self.__class__,)
        #print "h_tick: sec_count(%s) min_count(%s) hour_count(%s) day_count(%s)" % (sec_count, min_count, hour_count, day_count)
        #print "h_tick: sec(%s) min(%s) hour(%s) day(%s)" % (second_marker, min_marker, hour_marker, day_marker)
        if second_marker:
            self._processTimers(sec_count, "sec")
        if min_marker:
            self._processTimers(min_count, "min")
        if hour_marker:
            self._processTimers(hour_count, "hour")
        if day_marker:
            self._processTimers(day_count, "day")
        
    def _processTimers(self, count, base):
        for entry in self._timers[base]:
            interval, callback_name = entry
            if (count % interval==0):
                callback=getattr(self, callback_name)
                callback(base, count)
                

                


class AgentThreadedBridge(object):
    """
    Base class for agents bridging the "gobject world" (example)
    with the message based "mswitch world"
    
    *** NOT TESTED***
    """
    
    LOW_PRIORITY_MESSAGE_BURST_SIZE=5
    
    def __init__(self, time_base):
        """
        @param time_base: in milliseconds
        """
        self.time_base=time_base 
        self.ticks_second=1000/time_base

        self.iq=Queue()
        self.isq=Queue()
        mswitch.subscribe(self.iq, self.isq)

        self.tick_count=0
        self.sec_count=0
        self.min_count=0
        self.hour_count=0
        self.day_count=0
        
    def on_destroy(self):
        """
        Can be subclassed if any processing needs to
        occur before terminating the thread
        """
        pass
        
    def tick(self, *_):
        """
        Performs message dispatch
        """
        tick_min=False
        tick_hour=False
        tick_day=False
        tick_second = (self.tick_count % self.ticks_second) == 0 
        self.tick_count += 1
        
        if tick_second:
            self.sec_count += 1

            tick_min=(self.sec_count % 60)==0
            if tick_min:
                self.min_count += 1
                
                tick_hour=(self.min_count % 60)==0
                if tick_hour:
                    self.hour_count += 1
                    
                    tick_day=(self.hour_count % 24)==0
                    if tick_day:
                        self.day_count += 1
        
        #print "tick! ", tick_second
        mswitch.publish("__main__", "__tick__", self.ticks_second, 
                        tick_second, tick_min, tick_hour, tick_day, 
                        self.sec_count, self.min_count, self.hour_count, self.day_count)
        
        while True:
            try:     
                envelope=self.isq.get(False)
                quit, mtype, handled=mdispatch(self, "__main__", envelope)
                if handled==False:
                    mswitch.publish(self.__class__, "__interest__", mtype, False, False, self.isq)
                if quit:
                    self.on_destroy()
                    break
                
            except Empty:
                break
            continue            
        
        burst=self.LOW_PRIORITY_MESSAGE_BURST_SIZE
        
        while True:
            try:     
                envelope=self.iq.get(False)
                quit, mtype, handled=mdispatch(self, "__main__", envelope)
                if handled==False:
                    mswitch.publish(self.__class__, "__interest__", mtype, False, False, self.iq)
                if quit:
                    self.on_destroy()
                    break
                    
                burst -= 1
                if burst == 0:
                    break
            except Empty:
                break
            
            continue

        ## Integration with gobject requires this
        return True


class TickGenerator(object):
    def __init__(self, ticks_second, publisher):
        self.ticks_second=ticks_second
        self.publisher=publisher

        self.tick_count=0
        self.sec_count=0
        self.min_count=0
        self.hour_count=0
        self.day_count=0
        
    def input(self):
        """
        Performs message dispatch
        """
        tick_min=False
        tick_hour=False
        tick_day=False
        tick_second = (self.tick_count % self.ticks_second) == 0 
        self.tick_count += 1
        
        if tick_second:
            self.sec_count += 1

            tick_min=(self.sec_count % 60)==0
            if tick_min:
                self.min_count += 1
                
                tick_hour=(self.min_count % 60)==0
                if tick_hour:
                    self.hour_count += 1
                    
                    tick_day=(self.hour_count % 24)==0
                    if tick_day:
                        self.day_count += 1
        
        #print "tick! ", tick_second
        self.publisher(self.ticks_second, 
                        tick_second, tick_min, tick_hour, tick_day, 
                        self.sec_count, self.min_count, self.hour_count, self.day_count)
        
        ## just in case this is used along with gobject...
        return True
    

def custom_dispatch(source, q, pq, dispatcher, low_priority_burst_size=5):
    """
    For customer dispatching
    
    @param source: identifier for 'source'
    @param low_priority_burst_size: integer, maximum size of normal queue processing at a time 
    @param q: normal queue
    @param pq: priority queue
    @param dispatcher: callable
    """
    while True:
        try:     
            envelope=pq.get(False)
            orig, mtype, payload = envelope
            pargs, _kargs = payload
            
            ## skip self
            if orig==source:
                continue
            handled, snooping=dispatcher(mtype, *pargs)
            if handled==False:
                print "* '%s': not interest in '%s' message type" % (orig, mtype)
                mswitch.publish(source, "__interest__", source, mtype, False, snooping, pq)
                break
        except Empty:
            break
        continue            
    
    burst=low_priority_burst_size
    
    while True:
        try:     
            envelope=q.get(False)
            orig, mtype, payload = envelope
            pargs, _kargs = payload

            ## skip self
            if orig==source:
                continue
            handled, snooping=dispatcher(mtype, *pargs)
            if handled==False:
                print "* '%s': not interest in '%s' message type" % (orig, mtype)
                mswitch.publish(source, "__interest__", source, mtype, False, snooping, q)
            burst -= 1
            if burst == 0:
                break
        except Empty:
            break
        
        continue
    

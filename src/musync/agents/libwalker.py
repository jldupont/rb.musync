"""
    LibWalker Agent
    
    Responsible for traversing the RB database and pull the "ratings"
    information from 'musync' through DBus.
    
    
    Messages In:
    - "song_entries"
    - "entry_added"
    - "rb_shell"
    - "__tick__"

    
    Messages Out:
    - "libwalker_start"
    - "libwalker_done"
    
    
    @author: jldupont
    @date: Jun 4, 2010
"""
from musync.system.mbus import Bus
from musync.helpers.db import EntryHelper

from musync.helpers.state import StateManager

class LibWalker(object):

    ### libwalk period
    WALKING_TIMEOUT=24*60*60

    def __init__(self):
        self.song_entries=[]
        self.rated_song_count=None
        
        self.load_completed=False
        self.appname=None
        
        self.state="wait_load_completed"
        self.musync_detected=False
        self.musync_lastest_timestamp=None
        self.musync_lastest_ratings_count=None
        
        
        Bus.subscribe(self.__class__, "__tick__",           self.h_tick)
        Bus.subscribe(self.__class__, "rb_shell",           self.h_rb_shell)
        Bus.subscribe(self.__class__, "rb_load_completed",  self.h_rb_load_completed)
        Bus.subscribe(self.__class__, "musync_in_updated",  self.h_musync_in_updated)
        Bus.subscribe(self.__class__, "entry_added",        self.h_entry_added)
        Bus.subscribe(self.__class__, "entry_changed",      self.h_entry_changed)
        Bus.subscribe(self.__class__, "entry_deleted", self.h_entry_deleted)
        Bus.subscribe(self.__class__, "appname",       self.h_appname)
        Bus.subscribe(self.__class__, "devmode",       self.h_devmode)

        ## get configuration, the tricky way ;-)
        Bus.publish(self.__class__, "appname?")
        Bus.publish(self.__class__, "devmode?")
        
        self.sm=StateManager(self.appname)
        
    ## ========================================================================= handlers
    def h_appname(self, appname):
        self.appname=appname

    def h_devmode(self, devmode):
        self.devmode=devmode

    def h_entry_added(self, rbid, entry):
        self.song_entries[rbid]=(None, None)
    
    def h_entry_deleted(self, rbid, entry):
        try:   
            del self.song_entries[rbid]
        except:
            self.pub("llog", "err/", "error", "Tried deleting an entry from song_entries")

    def h_entry_changed(self, rbid, entry, changes):
        self.dprint("! Changes: %s" % changes)

    def h_rb_shell(self, _shell, db, _sp):
        """
        Grab RB objects references (shell, db, player)
        """
        self.db=db

    def h_rb_load_completed(self, entries):
        """
        Database fully loaded - the load on RB should have dropped
        """
        self.load_completed=True
        self.song_entries=entries
        
        self.rated_song_count = 0
        for _rbid, entry in entries.iteritems():
            _playcount, rating=entry
            if rating > 0:
                self.rated_song_count += 1
     
        print("! found %s tracks with a rating" % self.rated_song_count)

    def h_tick(self, ticks_second, 
                    tick_second, tick_min, tick_hour, tick_day, 
                    sec_count, min_count, hour_count, day_count):
        """
        'tick' timebase handler
        """
        ### Dispatch based on the state variable
        try:
            if tick_min:
                getattr(self, "st_"+self.state)()
        except Exception,e:
            print "!!! Attempted to dispatch, state: %s, exception: %s" % (self.state, e)
            

    ## =========
    ## from musync
    def h_musync_in_updated(self, timestamp, count):
        self.musync_detected=True
        self.musync_lastest_timestamp=timestamp
        self.musync_lastest_ratings_count=count
            
     
    ## =========================================================================
    ## STATE MACHINE
    def st_wait_load_completed(self):
        """
        Wait until the rb database is fully loaded
        """
        if self.load_completed:
            ### must have musync available or else what's the point?
            if not self.musync_detected:
                return
            
            print "libwalker: musync_detected"
            
            ### hmmm.... can't take a stand right now either...
            if self.rated_song_count is None or self.rated_song_count==0:
                return
            
            print "libwalker: ratings found"

            if self.musync_lastest_ratings_count==0:
                self.state="push_mode"
            else:
                self.state="pull_mode"

    def st_push_mode(self):
        """
        MuSync seems empty... populate it!
        """
        print "libwalker: PUSH MODE"
        
    def st_pull_mode(self):
        """
        Normal operation mode - pull updates from MuSync
        """
        print "libwalker: PULL MODE"
     

_=LibWalker()


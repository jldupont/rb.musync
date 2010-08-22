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
        self.load_completed=False
        self.appname=None
        
        Bus.subscribe(self.__class__, "__tick__",      self.h_tick)
        Bus.subscribe(self.__class__, "rb_shell",      self.h_rb_shell)
        Bus.subscribe(self.__class__, "song_entries",  self.h_song_entries)
        Bus.subscribe(self.__class__, "entry_added",   self.h_entry_added)
        Bus.subscribe(self.__class__, "entry_changed", self.h_entry_changed)
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
        pass
    
    def h_entry_deleted(self, rbid, entry):
        pass

    def h_entry_changed(self, rbid, entry):
        pass


    def h_song_entries(self, entries):
        self.song_entries=entries

    def h_rb_shell(self, _shell, db, _sp):
        """
        Grab RB objects references (shell, db, player)
        """
        self.db=db

    def h_rb_load_completed(self, *_):
        """
        Database fully loaded - the load on RB should have dropped
        """
        self.load_completed=True

    def h_tick(self, ticks_second, 
                    tick_second, tick_min, tick_hour, tick_day, 
                    sec_count, min_count, hour_count, day_count):
        """
        'tick' timebase handler
        """
     
    ## ========================================================================= helpers
     

     
     

_=LibWalker()


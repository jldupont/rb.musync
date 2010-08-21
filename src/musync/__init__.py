"""
    MuSync - Rhythmbox plugin

    @author: Jean-Lou Dupont
    

    MESSAGES GENERATED:
    ===================
    - "tick"
    - "tick_params"
    - "load_complete"
    - "song_entries"
    - "rb_shell"
    - "entry_added"
    - "track?"

    
"""
DEV_MODE=True
PLUGIN_NAME="musync"
TICK_FREQ=4
TIME_BASE=250

import os
import sys

curdir=os.path.dirname(__file__)
sys.path.insert(0, curdir)
print curdir

import gobject
import dbus.glib
from dbus.mainloop.glib import DBusGMainLoop

gobject.threads_init()  #@UndefinedVariable
dbus.glib.init_threads()
DBusGMainLoop(set_as_default=True)


import rhythmdb, rb #@UnresolvedImport

from system.base import TickGenerator
from system.mbus import Bus
from helpers.db import EntryHelper

from config import ConfigDialog

import system.base as base
base.debug=DEV_MODE

import system.mswitch
import agents.bridge
import agents.mb
import agents.monitor
#import agents.libwalker

import agents._tester


class Plugin (rb.Plugin):
    """
    Must derive from rb.Plugin in order
    for RB to use the plugin
    """
    def __init__ (self):
        rb.Plugin.__init__ (self)
        self.current_entry=None
        self.dbcount=0
        self.load_complete=False
        self.done=False
        self.db=None
        self.type_song=None
        self.start_phase=True
        self.current_entries_count=0
        self.previous_entries_count=0
        
        Bus.subscribe("__pluging__", "__tick__", self.h_tick)

    def activate (self, shell):
        """
        Called by Rhythmbox when the plugin is activated
        """
        self.shell = shell
        self.sp = shell.get_player()
        self.db=self.shell.props.db
        
        ## We might have other signals to connect to in the future
        self.dbcb = (
                     #self.db.connect("entry-added",    self.on_entry_added),
                     self.db.connect("entry-changed",  self.on_entry_changed),
                     self.db.connect("load-complete",  self.on_load_complete),
                     )
        ## Distribute the vital RB objects around
        Bus.publish("__pluging__", "rb_shell", self.shell, self.db, self.sp)
        
        self.type_song=self.db.entry_type_get_by_name("song")
        
    def deactivate (self, shell):
        """
        Called by RB when the plugin is about to get deactivated
        """
        self.shell = None
        db = shell.props.db
        
        for id in self.dbcb:
            db.disconnect(id)

    def create_configure_dialog(self, dialog=None):
        """
        This method is called by RB when "configure" button
        is pressed in the "Edit->Plugins" menu.
        
        Note that the dialog *shouldn't* be destroyed but "hidden" 
        when either the "close" or "X" buttons are pressed.
        """
        if not dialog:
            glade_file_path=self.find_file("config.glade")
            proxy=ConfigDialog(glade_file_path)
            dialog=proxy.get_dialog() 
        dialog.present()
        Bus.publish("__pluging__", "config?")
        return dialog

    ## ================================================  rb signal handlers
    
    def on_load_complete(self, *_):
        """
        'load-complete' signal handler
        """
        self.load_complete=True
        Bus.publish("__pluging__", "load_complete")

    def h_tick(self, ticks_per_second, 
               second_marker, min_marker, hour_marker, day_marker,
               sec_count, min_count, hour_count, day_count):

        """        
        if min_marker:
            print "current(%s) previous(%s)" % (self.current_entries_count, self.previous_entries_count)
        """

        if second_marker:
            if self.start_phase:
                if self.previous_entries_count==self.current_entries_count:
                    if self.current_entries_count!=0:
                        self.start_phase=False
                        Bus.publish("__pluging__", "rb_load_completed")
                self.previous_entries_count=self.current_entries_count
        

    def on_entry_changed(self, _db, entry, _):
        """
        'entry-changed' signal handler
        
        This handler is also called during the start-up phase of RB... quite annoying
        """
        if not self.start_phase:
            type=entry.get_entry_type()
            if type==self.type_song:
                dict_entry=EntryHelper.track_details2(self.db, entry)
                Bus.publish("__main__", "entry_changed", dict_entry)
        
        if self.start_phase:
            self.current_entries_count+=1


def tick_publisher(*p):
    Bus.publish("__main__", "__tick__", *p)

_tg=TickGenerator(1000/TIME_BASE, tick_publisher)
gobject.timeout_add(TIME_BASE, _tg.input)


"""
dir(rhythmdb):
['ENTRY_CONTAINER', 'ENTRY_NORMAL', 'ENTRY_STREAM', 'ENTRY_VIRTUAL', 
'Entry', 'EntryCategory', 'EntryType', 'ImportJob', 

'PROPERTY_MODEL_COLUMN_NUMBER', 'PROPERTY_MODEL_COLUMN_PRIORITY', 
'PROPERTY_MODEL_COLUMN_TITLE', 

'PROP_ALBUM', 'PROP_ALBUM_FOLDED', 
'PROP_ALBUM_GAIN', 'PROP_ALBUM_PEAK', 'PROP_ALBUM_SORTNAME', 'PROP_ALBUM_SORT_KEY', 
'PROP_ARTIST', 'PROP_ARTIST_FOLDED', 'PROP_ARTIST_SORTNAME', 'PROP_ARTIST_SORT_KEY', 
'PROP_BITRATE', 'PROP_COPYRIGHT', 'PROP_DATE', 'PROP_DESCRIPTION', 'PROP_DISC_NUMBER', 
'PROP_DURATION', 
'PROP_ENTRY_ID', 'PROP_FILE_SIZE', 'PROP_FIRST_SEEN', 
'PROP_FIRST_SEEN_STR', 'PROP_GENRE', 'PROP_GENRE_FOLDED', 'PROP_GENRE_SORT_KEY', 
'PROP_HIDDEN', 'PROP_IMAGE', 'PROP_KEYWORD', 'PROP_LANG', 
'PROP_LAST_PLAYED', 'PROP_LAST_PLAYED_STR', 
'PROP_LAST_SEEN', 'PROP_LAST_SEEN_STR', 
'PROP_LOCATION', 'PROP_MIMETYPE', 'PROP_MOUNTPOINT', 'PROP_MTIME', 
'PROP_MUSICBRAINZ_ALBUMARTISTID', 'PROP_MUSICBRAINZ_ALBUMID', 'PROP_MUSICBRAINZ_ARTISTID', 'PROP_MUSICBRAINZ_TRACKID', 
'PROP_PLAYBACK_ERROR', 'PROP_PLAY_COUNT', 'PROP_POST_TIME', 'PROP_RATING', 
'PROP_SEARCH_MATCH', 'PROP_STATUS', 'PROP_SUBTITLE', 'PROP_SUMMARY', 'PROP_TITLE', 
'PROP_TITLE_FOLDED', 'PROP_TITLE_SORT_KEY', 'PROP_TRACK_GAIN', 'PROP_TRACK_NUMBER', 
'PROP_TRACK_PEAK', 'PROP_TYPE', 'PROP_YEAR', 

'PropType', 'PropertyModel', 'PropertyModelColumn', 

'QUERY_DISJUNCTION', 'QUERY_END', 'QUERY_MODEL_LIMIT_COUNT', 'QUERY_MODEL_LIMIT_NONE', 
'QUERY_MODEL_LIMIT_SIZE', 'QUERY_MODEL_LIMIT_TIME', 'QUERY_PROP_CURRENT_TIME_NOT_WITHIN', 
'QUERY_PROP_CURRENT_TIME_WITHIN', 'QUERY_PROP_EQUALS', 'QUERY_PROP_GREATER', 
'QUERY_PROP_LESS', 'QUERY_PROP_LIKE', 'QUERY_PROP_NOT_LIKE', 'QUERY_PROP_PREFIX', 
'QUERY_PROP_SUFFIX', 'QUERY_PROP_YEAR_EQUALS', 'QUERY_PROP_YEAR_GREATER', 
'QUERY_PROP_YEAR_LESS', 'QUERY_SUBQUERY', 

'Query', 'QueryModel', 'QueryModelLimitType', 'QueryResults', 'QueryType', 'RhythmDB', 
'StringValueMap', '__doc__', '__name__', '__package__', '__version__', 
'rhythmdb_compute_status_normal', 'rhythmdb_query_model_album_sort_func', 
'rhythmdb_query_model_artist_sort_func', 'rhythmdb_query_model_date_sort_func', 
'rhythmdb_query_model_double_ceiling_sort_func', 'rhythmdb_query_model_genre_sort_func', 
'rhythmdb_query_model_location_sort_func', 'rhythmdb_query_model_string_sort_func', 
'rhythmdb_query_model_title_sort_func', 'rhythmdb_query_model_track_sort_func', 
'rhythmdb_query_model_ulong_sort_func']
"""
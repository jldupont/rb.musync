"""
    Musicbrainz Agent
    
    Responsible for fetching the UUID associated with tracks
    from the Musicbrainz Proxy DBus application
    
    * The currently playing is examined for a "track mbid":
      if this UUID isn't found, try fetching it from MB Proxy
      
    
    MESSAGES IN:
    - "rb_shell"
    - "track?"
    - "ctrack"   (mainly from lastfm_proxy)
    
    
    MESSAGES OUT:
    - "musicbrainz_proxy_detected"
    - "mb_track"
    
    Fields returned by Musicbrainz Proxy:
     - "artist_name"
     - "track_name"
     - "artist_mbid"
     - "track_mbid"
     - "mb_artist_name"
     - "mb_track_name"
    
    @author: jldupont
    @date: May 31, 2010
"""
import dbus.service

from sync_ratings.system.base import AgentThreadedBase

class DbusInterface(dbus.service.Object):
    """
    DBus interface - listening for signals from Musicbrainz Proxy DBus
    """
    PATH="/Tracks"
    
    def __init__(self, agent):
        dbus.service.Object.__init__(self, dbus.SessionBus(), self.PATH)
        self.agent=agent
        dbus.Bus().add_signal_receiver(self.sTracks, 
                               signal_name="Tracks", 
                               dbus_interface="com.jldupont.musicbrainz.proxy", 
                               bus_name=None, 
                               path="/Tracks")


    @dbus.service.signal(dbus_interface="com.jldupont.musicbrainz.proxy", signature="vvvv")
    def qTrack(self, _ref, _artist_name, _track_name, _priority):
        """
        Signal Emitter - qTrack
        """

    def sTracks(self, source, ref, tracks):
        """
        Signal Receptor - Track
        
        Verify the "ref" parameter to make sure it is
        in reponse to a 'question' we asked
        """
        rb=False
        ukey=None
        
        try:    
            rbstr, ukey=ref.split(":")
            rb=(rbstr=="rb_sync_ratings")
        except:
            rb=False

        ## we are not interested in response to requests of others
        if not rb:
            return

        self.agent.pub("mb_tracks", source, ref, ukey, tracks)
            
        self.agent.pub("mb_detected", True)
        self.agent.detected=True
        





class MBAgent(AgentThreadedBase):

    def __init__(self): 
        AgentThreadedBase.__init__(self)
        self.dbusif=DbusInterface(self)
        self.detected=False
        
    def h_tick_params(self, *_):
        """
        Kickstart
        """
        self.dbusif.qTrack("rb", "Depeche Mode", "Little 15", "low")
        
    def hq_mb_detected(self):
        self.pub("mb_detected", self.detected)
        
    def hq_track(self, track):
        """
        Helps the track resolving functionality
        """
        self.h_ctrack(None, track, "high")

        
## Kick start the agent        
_=MBAgent()
_.start()

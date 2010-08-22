"""
    Musync Agent Dbus
    
    Messages Processed:
    ==================
    - "qrating"
    - "qratings"
    - "out_rating"
    
    Messages Generated:
    ===================
    - "musync_in_updated"
    - "musync_in_rating"
    
    
    @author: jldupont
    @date: August 2010
"""
import dbus.service

from musync.system.base import AgentThreadedBase
from musync.system import mswitch

class DbusInterface(dbus.service.Object):
    """
    DBus interface - listening for signals from Musync application
    """
    PATH="/ratings"
    
    def __init__(self, agent):
        dbus.service.Object.__init__(self, dbus.SessionBus(), self.PATH)
        self.agent=agent
        self.detected=False

        dbus.Bus().add_signal_receiver(self.rx_rating,
                                       signal_name="rating",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )
        
        dbus.Bus().add_signal_receiver(self.rx_updated,
                                       signal_name="updated",
                                       dbus_interface="com.systemical.services",
                                       bus_name=None,
                                       path="/ratings"
                                       )
        
    def rx_rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        """
        'rating' signal from Musync
        """
        mswitch.publish("__musync_dbus__", "musync_in_rating", source, ref, timestamp, artist_name, album_name, track_name, rating)
        
        
    def rx_updated(self, timestamp, ratings_count):
        """
        Signal emitter for "/ratings/updated"
        """
        mswitch.publish("__musync_dbus__", "musync_in_updated", timestamp, ratings_count)
        self.detected=True

    ## ================================================================
    ## Emitters
    @dbus.service.signal(dbus_interface="com.systemical.services", signature="sssss")
    def qrating(self, source, ref, artist_name, album_name, track_name):
        """
        'qratings' signal emitter
        """
    
    @dbus.service.signal(dbus_interface="com.systemical.services", signature="ssii")
    def qratings(self, source, ref, timestamp, count):
        """
        'qratings' signal emitter
        """

    @dbus.service.signal(dbus_interface="com.systemical.services", signature="ssisssd")
    def rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        """
        'rating' signal emitter
        """
        


class MusyncAgent(AgentThreadedBase):

    def __init__(self): 
        AgentThreadedBase.__init__(self)
        self.dif=DbusInterface(self)
        self.detected=False
        
    def hq_qratings(self, source, ref, timestamp, count):
        self.dif.qratings(source, ref, timestamp, count)

    def h_out_rating(self, source, ref, timestamp, artist_name, album_name, track_name, rating):
        self.dif.rating(source, ref, timestamp, artist_name, album_name, track_name, rating)

    def hq_qrating(self, source, ref, artist_name, album_name, track_name):
        self.dif.qrating(source, ref, artist_name, album_name, track_name)

        
## Kick start the agent        
_=MusyncAgent()
_.start()

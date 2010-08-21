"""
    State Agent
    
    Maintains state information in the gnome configuration registry
    
    MESSAGES IN:
    
    MESSAGES OUT:


    @author: jldupont
    @date: May 27, 2010
"""
import gconf

class StateManager(object):
    
    PATH_TEMPLATE="/apps/rhythmbox/%s/"
        
    def __init__(self, app_name):
        self.app_name=app_name
        self.gclient=gconf.client_get_default()
        self.path=(self.PATH_TEMPLATE % app_name) + "%s"
        
    def save(self, key, value):
        if isinstance(value, int):
            self.gclient.set_int(self.path % key, value)
        elif isinstance(value, float):
            self.gclient.set_float(self.path % key, value)
        else:
            self.gclient.set_string(self.path % key, str(value))
    
    def retrieve(self, key):
        try:    
            value=self.gclient.get_int(self.path % key)
        except:
            value=None
            try:
                value=self.gclient.get_string(self.path % key)
            except:
                value=self.gclient.get_float(self.path % key)
        return value
    

if __name__=="__main__":
    sm=StateManager("test")
    sm.save("a_float", 6.66)
    sm.save("an_int", 666)
    sm.save("a_string", "666")

    print sm.retrieve("a_float")
    print sm.retrieve("an_int")
    print sm.retrieve("a_string")
    
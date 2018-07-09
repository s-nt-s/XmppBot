#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import sys
from geopy.geocoders import Nominatim

import requests
from xmppbot import XmppBot, botcmd

#map_url = "http://tyler-demo.herokuapp.com/?lat={lat}&lon={lon}&width=3000&height=1688&zoom=19"
map_prm_1 = "&width=3000&height=3000&zoom=19"
map_url_1 = "http://tyler-demo.herokuapp.com/?lat={lat}&lon={lon}" + map_prm_1
map_prm_2 = "size=1024x1024&maptype=mapnik&zoom=18"
map_url_2 = "http://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}" + map_prm_2

class MapBot(XmppBot):

    '''
    def __init__(self, *args, **kwargs):
        XmppBot.__init__(self, *args, **kwargs)
        self.use_ipv6 = False
    '''

    def start(self, event):
        super().start(event)
        self.register_plugin('xep_0066') # OOB
        self.register_plugin('xep_0231') # BOB

    def send_oob(self, user, url):
        m = self.Message()
        m['to'] = user
        m['type'] = 'chat'
        m['oob']['url'] = url
        m.send()

    @botcmd(regex=re.compile(r'^(.+)$'), rg_mode="match")
    def direccion(self, calle, user, **kwargs):
        location = Nominatim().geocode(calle)
        if not location:
            return "No encontrado"
        url_1 = map_url_1.format(lat=location.latitude, lon=location.longitude)
        url_2 = map_url_2.format(lat=location.latitude, lon=location.longitude)
        
        self.send_oob(user, url_1.replace(map_prm_1, "")+"&greyscale=true")
        self.send_oob(user, url_2)

        return location.address+"\n" + url_1 + "\n" + url_2
        
if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = MapBot("map.yaml")
    xmpp.run()

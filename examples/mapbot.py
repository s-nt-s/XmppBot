#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

import requests
from geopy.geocoders import Nominatim

from xmppbot import XmppBot, botcmd

#map_url = "http://tyler-demo.herokuapp.com/?lat={lat}&lon={lon}&width=3000&height=1688&zoom=19"
map_prm_1 = "&width=3000&height=3000&zoom=19"
map_url_1 = "http://tyler-demo.herokuapp.com/?lat={lat}&lon={lon}" + map_prm_1
map_prm_2 = "&size=1024x1024&maptype=mapnik&zoom=18"
map_url_2 = "http://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&markers={lat},{lon},lightblue1" + map_prm_2


class MapBot(XmppBot):

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
            return "Not found"
        url_1 = map_url_1.format(lat=location.latitude, lon=location.longitude)
        url_2 = map_url_2.format(lat=location.latitude, lon=location.longitude)

        self.send_oob(user, url_1.replace(map_prm_1, "")+"&greyscale=true")
        self.send_oob(user, url_2)  # .replace(map_prm_2, ""))

        return location.address+"\n" + url_1 + "\n" + url_2


if __name__ == '__main__':
    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    xmpp = MapBot("map.yml")
    xmpp.run()

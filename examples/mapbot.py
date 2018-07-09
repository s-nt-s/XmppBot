#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import sys
from geopy.geocoders import Nominatim

import requests
from xmppbot import XmppBot, botcmd

map_url = "http://tyler-demo.herokuapp.com/?lat={lat}&lon={lon}&width=3000&height=1688&zoom=19"

class MapBot(XmppBot):

    @botcmd(regex=re.compile(r'^(.+)$'), rg_mode="match")
    def direccion(self, calle, **kwargs):
        location = Nominatim().geocode(calle)
        if not location:
            return "No encontrado"
        url = map_url.format(lat=location.latitude, lon=location.longitude)
        #return url
        return location.address+"\n" + url
        
    def format_message(self, txt, *args, **kwargs):
        return None
        url = txt.split("\n")[-1]
        if url.startswith("http://"):
            txt=txt+"\n<img src='"+url+"'/>"
        txt = "<span style='font-family: monospace'>" + txt.replace("\n", "<br/>") + "</span>"
        return txt

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = MapBot("map.yaml")
    xmpp.run()

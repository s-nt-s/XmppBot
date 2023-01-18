#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

import requests

from xmppbot import XmppBot, botcmd

min_long = str(3)
max_long = str(100)

API_URL = "https://es.wikipedia.org/w/api.php"
API_ARG = {
    'format': 'json',
    'action': 'query',
    'pithumbsize': 240,
    'redirects': '',
    'explaintext': '',
    'exintro': '',
    'inprop': 'url',
    'prop': 'info|pageimages|extracts',
    'titles': ''
}


requests.packages.urllib3.disable_warnings()


class WikiPedia:
    def __init__(self, busqueda):
        API_ARG["titles"] = busqueda
        r = requests.get(API_URL, params=API_ARG, verify=False)
        j = r.json()
        j = j["query"]
        j = j["pages"]
        k = j.keys()
        self.ko = '-1' in k
        if not self.ko:
            j = next(iter(j.values()))
            self.pageid = j["pageid"]
            self.title = j["title"]
            self.image = j["thumbnail"]["source"] if "thumbnail" in j else None
            self.summary = j["extract"]
            self.url = j["canonicalurl"]


class WikiBot(XmppBot):

    def start(self, event):
        super().start(event)
        self.register_plugin('xep_0066')  # OOB
        self.register_plugin('xep_0231')  # BOB

    @botcmd(regex=re.compile(r'^(.{'+min_long+','+max_long+'})$'), rg_mode="match")
    def wikipedia(self, busqueda, user, **kwargs):
        w = WikiPedia(busqueda)
        if w.ko:
            return "Tu búsqueda no obtiene resultados."
        msg = ""
        if w.title.lower() != busqueda.lower():
            msg = msg+w.title+"\n"
        if w.image:
            m = self.Message()
            m['to'] = user
            m['type'] = 'chat'
            m['oob']['url'] = w.image
            m['body'] = w.image
            m.send()
        msg = msg+w.summary
        msg = msg+"\nFuente: "+w.url
        return msg

    @botcmd(regex=re.compile(r'^(.+)$'), rg_mode="match")
    def anything_else(self, busqueda, **kwargs):
        return "Solo se admiten búsquedas de entre "+min_long+" y "+max_long+" caracteres"


if __name__ == '__main__':
    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    os.chdir(path)
    xmpp = WikiBot("wiki.yml")
    xmpp.run()

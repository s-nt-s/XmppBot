#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
import sys

import requests
from xmppbot import XmppBot, botcmd

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

min_long=str(3)
max_long=str(100)

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
        API_ARG["titles"]=busqueda
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
        
def get_options(b,ops):
    b = b.lower()
    ops = [i for i in set(ops) if i.lower() != b]
    if len(ops) == 0:
        return None
    return sorted(ops)

class WikiBot(XmppBot):

    @botcmd(regex=re.compile(r'^(.{'+min_long+','+max_long+'})$'), rg_mode="match")
    def wikipedia(self, user, busqueda, args):
        w = WikiPedia(busqueda)
        if w.ko:
            return "Tu búsqueda no obtiene resultados."
        msg=""
        if w.title.lower() != busqueda.lower():
            msg = msg+w.title+"\n"
        if w.image:
            msg = msg+w.image+"\n"
        msg = msg+w.summary
        msg = msg+"\nFuente: "+w.url
        return msg
        
    @botcmd(regex=re.compile(r'^(.+)$'), rg_mode="match")
    def todo_lo_demas(self, user, busqueda, args):
        return "Solo se admiten búsquedas de entre "+min_long+" y "+max_long+" caracteres"

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = WikiBot("wiki.yaml")
    xmpp.run()

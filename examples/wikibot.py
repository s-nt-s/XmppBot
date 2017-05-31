#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import logging
import requests
import wikipedia

from xmppbot import botcmd, XmppBot

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')


min_long=str(3)
max_long=str(100)

def get_image(wiki_id):
    url="https://es.wikipedia.org/w/api.php?format=json&action=query&formatversion=2&pithumbsize=240&prop=pageimages&redirects&pageids="+wiki_id
    r = requests.get(url)
    j = r.json()
    j = j["query"]["pages"][0]
    if "thumbnail" in j:
        return j["thumbnail"]["source"]
    return None

class WikiBot(XmppBot):

    @botcmd(regex=re.compile(r'^(.{'+min_long+','+max_long+'})$'), rg_mode="match")
    def wikipedia(self, user, busqueda, args):
        try:
            r = wikipedia.page(busqueda,auto_suggest=True, redirect=True)
            msg=r.title+"\n"
            img = get_image(r.pageid)
            '''
            img = r.images[0] if r.images and len(r.images)>0 else None
            '''
            if img:
                msg = msg+img+"\n" #"<img src=\""+img+"\"/>\n"
            msg = msg+r.summary
            msg = msg+"\nFuente: "+r.url
            return msg
        except wikipedia.exceptions.DisambiguationError as e:
            return "Concrete la búsqueda:\n- " + "\n- ".join(e.options)
        except wikipedia.exceptions.PageError as e:
            return "Su búsqueda no da resultados"
        return None
        
    @botcmd(regex=re.compile(r'^(.+)$'), rg_mode="match")
    def todo_lo_demas(self, user, busqueda, args):
        return "Solo se admiten búsquedas de entre "+min_long+" y "+max_long+" caracteres"

if __name__ == '__main__':
    wikipedia.set_lang("es")
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = WikiBot("wiki.yaml")
    xmpp.run()

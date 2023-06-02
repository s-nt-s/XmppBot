#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import requests
import logging
import sys
from os.path import isfile, realpath, dirname
from readabilipy import simple_json_from_html_string
from markdownify import ATX, MarkdownConverter
from bs4 import BeautifulSoup, Tag
import re
from textwrap import dedent

from xmppbot import XmppBot, CmdFindAll, CmdDefault, Message

requests.packages.urllib3.disable_warnings()

re_br = re.compile(r"\s*\n\s*\n\s*")
re_lf = re.compile(r" +$", re.MULTILINE)

INLINE = tuple("u b strong em i del s strike span a".split())
BLOCK = tuple("ul ol li th td div caption p div h[1-6] blockquote".split())
TABLE = tuple("table tbody thead tfoot th td tr".split())
HEADS = tuple("h1 h2 h3 h4 h5 h6".split())


class Xep0393Converter(MarkdownConverter):
    """ Create XEP-0393 from html, see https://xmpp.org/extensions/xep-0393.html """
    IMG_SPLIT = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)

    def convert(self, html):
        if isinstance(html, (Tag, BeautifulSoup)):
            html = html.find("body") or html
            html = str(html)

        def notable(x):
            tag = x.group(1)
            if tag.lower() in TABLE:
                return x.group(0)
            return x.group(2)
        html = re.sub(
            r"<(\w+)\b[^>]*>(\s*)</\1>",
            notable,
            html,
            flags=re.IGNORECASE)
        for tag in ('ul', 'ol') + INLINE:
            html = re.sub(r"</" + tag + r">(\s*)<" +
                          tag + "[^>]*>", r"\1", html)
        for tag in INLINE:
            for r in (
                re.compile(r"(<" + tag + r"[^>]*>)(\s+)"),
                re.compile(r"(\s+)(</" + tag + r">)")
            ):
                html = r.sub(r"\2\1", html)
        for tag in BLOCK:
            html = re.sub(r"(<" + tag + r"[^>]*>)(\s+)", r"\1", html)
            html = re.sub(r"(\s+)(</" + tag + r">)", r"\2", html)
        soup = BeautifulSoup(html, 'html.parser')
        hcount = 0
        for h in HEADS:
            hs = soup.findAll(h)
            if not hs:
                continue
            hcount += 1
            for h in hs:
                h.name = "h" + str(hcount)
        html = str(soup)
        text = super().convert(html)
        text = re_br.sub("\n\n", text)
        text = re_lf.sub("", text)
        return text.strip()

    def convert_em(self, el, text, convert_as_inline):
        return '_%s_' % text if text else ''

    def convert_strong(self, el, text, convert_as_inline):
        return '*%s*' % text if text else ''

    def convert_s(self, el, text, convert_as_inline):
        return self.convert_del(el, text)

    def convert_strike(self, el, text, convert_as_inline):
        return self.convert_del(el, text)

    def convert_del(self, el, text, convert_as_inline):
        return '~%s~' % text if text else ''

    def convert_blockquote(self, el, text, convert_as_inline):
        text = text.strip()
        text = re_br.sub("\n\n", text)
        text = re_lf.sub("", text)
        return super().convert_blockquote(el, text, convert_as_inline)

    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src")
        if not src:
            return ''
        return Xep0393Converter.IMG_SPLIT + ' ' + \
            src + ' ' + Xep0393Converter.IMG_SPLIT

    def convert_br(self, el, text, convert_as_inline):
        return ""


def to_xep0393(html, **options):
    options["heading_style"] = options.get("heading_style", ATX)
    return Xep0393Converter(**options).convert(html)


def url_to_json(url):
    r = requests.get(url)
    js = simple_json_from_html_string(r.text, use_readability=True)
    return js


class ReadBot(XmppBot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_plugin('xep_0066')  # OOB
        self.register_plugin('xep_0231')  # BOB

    @CmdFindAll(
        r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
        delay=True)
    def urls(self, *urls, msg: Message):
        for url in urls:
            js = url_to_json(url)
            m = msg.reply()
            m['body'] = dedent(f'''
                ==============
                {js['title']}
                ==============
            ''').strip()
            m.send()
            plain = to_xep0393(js['content'])
            for i, block in enumerate(plain.split(Xep0393Converter.IMG_SPLIT)):
                block = block.strip()
                if i % 2 == 1:
                    m = msg.reply()
                    m['oob']['url'] = block
                    m['body'] = block
                    m.send()
                else:
                    m = msg.reply()
                    m['body'] = block
                    m.send()
        return None

    @CmdDefault()
    def anything_else(self):
        return "Solo se responde a urls"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    path = realpath(__file__)
    path = dirname(path)
    os.chdir(path)
    if len(sys.argv) < 2 or not isfile(sys.argv[1]):
        sys.exit("Need file config as parameter")
    xmpp = ReadBot(sys.argv[1])
    xmpp.run()

import re
from os.path import expanduser, isfile

import yaml
from bs4 import BeautifulSoup, Tag
from markdownify import ATX, MarkdownConverter


def get_config(path):
    if path is None:
        raise Exception("Config file is mandatory")
    if isinstance(path, dict):
        config = path
    elif isinstance(path, str):
        path = expanduser(path)
        if not isfile(path):
            raise Exception(path+" doesn't exist")
        with open(path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise Exception("Config must be str or dict")
    if "user" not in config or "pass" not in config:
        raise Exception("Missing key values")
    return config


re_br = re.compile(r"\s*\n\s*\n\s*")
re_lf = re.compile(r" +$", re.MULTILINE)


class Xep0393Converter(MarkdownConverter):
    """ Create XEP-0393 from html, see https://xmpp.org/extensions/xep-0393.html """

    def __init__(self, *args, **kargv):
        MarkdownConverter.__init__(self, *args, **kargv)

    def convert(self, html):
        if isinstance(html, (Tag, BeautifulSoup)):
            html = html.find("body") or html
            html = str(html)
        for tag in ('u', 'ul', 'ol', "b", "strong", "em", "i", "del", "s", "strike", "span", "a"):
            html = re.sub(r"</" + tag + r">(\s*)<" +
                          tag + "[^>]*>", r"\1", html)
        for tag in ("b", "strong", "em", "i", "del", "s", "strike", "span", "a"):
            for r in (
                re.compile(r"(<"+tag+r"[^>]*>)(\s+)"),
                re.compile(r"(\s+)(</"+tag+r">)")
            ):
                html = r.sub(r"\2\1", html)
        for tag in ('li', 'th', 'td', 'div', 'caption', "p", "div", "h[1-6]"):
            html = re.sub(r"(<"+tag+r"[^>]*>)(\s+)", r"\1", html)
            html = re.sub(r"(\s+)(</"+tag+r">)", r"\2", html)
        text = MarkdownConverter.convert(self, html)
        text = re_br.sub("\n\n", text)
        text = re_lf.sub("", text)
        return text.strip()

    def convert_em(self, el, text):
        return '_%s_' % text if text else ''

    def convert_strong(self, el, text):
        return '*%s*' % text if text else ''

    def convert_s(self, el, text):
        return self.convert_del(el, text)

    def convert_strike(self, el, text):
        return self.convert_del(el, text)

    def convert_del(self, el, text):
        return '~%s~' % text if text else ''


def to_xep0393(html, **options):
    options["heading_style"] = options.get("heading_style", ATX)
    return Xep0393Converter(**options).convert(html)

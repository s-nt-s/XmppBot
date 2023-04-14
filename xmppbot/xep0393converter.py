import re

from bs4 import BeautifulSoup, Tag
from markdownify import ATX, MarkdownConverter

re_br = re.compile(r"\s*\n\s*\n\s*")
re_lf = re.compile(r" +$", re.MULTILINE)


class Xep0393Converter(MarkdownConverter):
    """ Create XEP-0393 from html, see https://xmpp.org/extensions/xep-0393.html """

    def __init__(self, *args, **kvargs):
        MarkdownConverter.__init__(self, *args, **kvargs)

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

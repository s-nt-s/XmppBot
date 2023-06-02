from xmppbot import XmppBot, CmdDefault
from slixmpp.stanza import Message


class FakeBot(XmppBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, func in XmppBot.__dict__.items():
            if name.startswith('_XmppBot__') and callable(func):
                new_name = '__' + name.split('__', 1)[-1]
                setattr(
                    self,
                    new_name,
                    getattr(self, name)
                )

    @CmdDefault()
    def ping(self, *args, **kvarg):
        return ""


def build_msg(**kwargs):
    msg = Message()
    msg['from'] = 'from@xmpp.com'
    msg['to'] = 'to@xmpp.com'
    msg['type'] = 'chat'
    msg['body'] = "this is a message"
    for k, v in kwargs.items():
        msg[k.lstrip("_")] = v
    return msg


def test_is_from_me():
    bot = FakeBot({
        "user": "me@xmpp.com",
        "password": "xxx"
    })
    for _from, expected in {
        "me@xmpp.com": True,
        "not_me@xmpp.com": False
    }.items():
        bl = bot.__is_from_me(build_msg(
            _from=_from
        ))
        assert bl is expected, f"{bl} is {expected} <- from={_from}"


def test_is_weird_message():
    bot = FakeBot({
        "user": "me@xmpp.com",
        "password": "xxx"
    })
    for _body, expected in {
        "": True,
        None: True,
        "   ": True,
        "Hi": False
    }.items():
        bl = bot.__is_weird_message(build_msg(
            _body=_body
        ))
        assert bl is expected, f"{bl} is {expected} <- body={_body}"
    for _from, expected in {
        "": True,
        None: True,
        "from@xmpp.com": False
    }.items():
        bl = bot.__is_weird_message(build_msg(
            _from=_from
        ))
        assert bl is expected, f"{bl} is {expected} <- from={_from}"


def test_is_in_my_inbox():
    bot = FakeBot({
        "user": "me@xmpp.com",
        "password": "xxx",
        "lisent": ('chat',)
    })
    for _type, expected in {
        "chat": True,
        "groupchat": False
    }.items():
        bl = bot.__is_in_my_inbox(build_msg(
            _type=_type
        ))
        assert bl is expected, f"{bl} is {expected} <- type={_type}"
    bot = FakeBot({
        "user": "me@xmpp.com",
        "password": "xxx",
        "roster": ('in_roster@xmpp.com',)
    })
    for _from, expected in {
        "in_roster@xmpp.com": True,
        "not_in_roster@xmpp.com": False
    }.items():
        bl = bot.__is_in_my_inbox(build_msg(
            _from=_from
        ))
        assert bl is expected, f"{bl} is {expected} <- from={_from}"

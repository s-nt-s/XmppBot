from xmppbot import \
    XmppBot, CmdBot, CmdMatch, \
    CmdSearch, CmdFindAll, CmdDefault
from xmppbot.cmdbot import BadMessageArgument
from slixmpp.stanza import Message
import pytest


class FakeBot(XmppBot):
    REPLY = "args={}, kwargs={}"

    def read_message(self, **kwargs):
        self.reply = None
        msg = Message()
        for k, v in kwargs.items():
            msg[k.lstrip("_")] = v
        self.sent_menssage = msg
        super().read_message(msg)
        return self.reply

    def reply_message(self, msg, txt):
        self.reply = txt


def build_bot(config_path, cmd, *args, **kwargs):
    class Bot(FakeBot):
        @cmd(*args, **kwargs)
        def ping(self, *args, **kvarg):
            return Bot.REPLY.format(args, kvarg)

    obj = Bot(config_path)
    return obj


def buil_message(*args, **kwargs):
    msg = Message()
    for k, v in kwargs.items():
        msg[k.lstrip("_")] = v
    return msg


def test_cmdbot_not_for_me():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdBot, "ping")
    reply = bot.read_message(
        _to='two@xmpp.com',
        _from='me@xmpp.com',
        _type='chat',
        _body="this is a message"
    )
    assert reply is None


def test_cmdbot_wired_msg():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdBot, "ping")
    reply = bot.read_message(
        _to='one@xmpp.com',
        _from='me@xmpp.com',
        _type='chat',
        _body=""
    )
    assert reply is None


def test_cmdbot_name():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdBot)
    for body, expected in {
        "ko": None,
        "ping": FakeBot.REPLY.format(tuple(), {}),
        "ping pong": FakeBot.REPLY.format(('pong', ), {})
    }.items():
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_cmdbot_ok_names():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdBot, "ping1", "ping2")
    for body, expected in {
        "ping": None,
        "ping1": FakeBot.REPLY.format(('ping1', ), {}),
        "ping1 pong": FakeBot.REPLY.format(('ping1', 'pong'), {})
    }.items():
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_cmdmatch_ok():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdMatch, r"(match)(?P<ping>ping)")
    for body, expected in {
        "ping": None,
        "_matchping_": None,
        "matchping": FakeBot.REPLY.format(('match', 'ping'), {'ping': 'ping'})
    }.items():
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_cmdsearch_ok():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdSearch, r"(search)(?P<ping>ping)")
    rpl = FakeBot.REPLY.format(('search', 'ping'), {'ping': 'ping'})
    for body, expected in {
        "ping": None,
        "_searchping_": rpl,
        "searchping": rpl
    }.items():
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_cmdfindall_ok():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdFindAll, r"findallping.?")
    for body, expected in {
        "ping": None,
        "findallping1 findallping2": FakeBot.REPLY.format(
            ('findallping1', 'findallping2'), {})
    }.items():
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_cmddefault_ok():
    bot: XmppBot = build_bot({
        "user": "one@xmpp.com",
        "password": "xxx"
    }, CmdDefault)
    for body in ("ping", "pong", "ping pong"):
        reply = bot.read_message(
            _to='one@xmpp.com',
            _from='me@xmpp.com',
            _type='chat',
            _body=body
        )
        expected = FakeBot.REPLY.format(tuple(body.strip().split()), {})
        if expected is None:
            assert reply is None
        else:
            assert reply == expected


def test_add_paramters():
    config = {
        "user": "one@xmpp.com",
        "password": "xxx",
        "admin": "me@xmpp.com"
    }

    with pytest.raises(BadMessageArgument):
        class BotKO1(FakeBot):
            @CmdDefault()
            def ping(self, a, b: Message, **kwarg):
                return b

    with pytest.raises(BadMessageArgument):
        class BotKO2(FakeBot):
            @CmdDefault()
            def ping(self, a: Message, *args, b: Message = None, **kwarg):
                return a

    class Bot2(FakeBot):
        @CmdDefault()
        def ping(self, b: Message, *args):
            return b

    bot = Bot2(config)
    reply = bot.read_message(
        _to='one@xmpp.com',
        _from='me@xmpp.com',
        _type='chat',
        _body="hi hi hi hi"
    )

    assert bot.sent_menssage == reply

    class Bot3(FakeBot):
        @CmdDefault()
        def ping(self, *args, a: Message = None, **kwargs):
            return a

    bot = Bot3(config)
    reply = bot.read_message(
        _to='one@xmpp.com',
        _from='me@xmpp.com',
        _type='chat',
        _body="hi hi hi hi"
    )

    assert bot.sent_menssage == reply

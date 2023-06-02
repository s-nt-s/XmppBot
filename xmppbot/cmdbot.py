from __future__ import annotations

import re
from inspect import getfullargspec

from .basebot import Message
from .common import to_tuple
from slixmpp.stanza import Message as sliMessage

re_sp = re.compile(r"\s+")


class NotForMeException(Exception):
    pass


class BadMessageArgument(Exception):
    pass


def countitems(*args):
    count = 0
    for a in args:
        if a is not None:
            if hasattr(a, "__len__"):
                count += len(a)
            else:
                count += 1
    return count


class CmdBot:
    INDEX = 0

    def __init__(
            self,
            *names: str,
            delay: bool = False,
            users: str | list[str] = None):
        CmdBot.INDEX += 1
        self.index = CmdBot.INDEX
        self.func = None
        self.delay = delay
        self.users = to_tuple(users)
        self.__name = names
        self.msg_parameter = None
        self.need_arguments = True
        self.__validate()

    def __validate(self):
        for n in self.__name:
            if not isinstance(n, str) or len(n.split()) > 1:
                raise ValueError("name must to be a str without spaces")

    def is_for_me(self, msg: Message) -> bool:
        if not callable(self.func):
            raise Exception("func is not callable")
        if not (self.delay) and msg.is_delay:
            return False
        if self.users and msg.sender not in self.users:
            return False
        try:
            self.extract_args(msg.text)
        except NotForMeException:
            return False
        return True

    def __call__(self, func):
        self.func = func
        self.__review_parameters()
        setattr(func, 'cmd', self)
        return func

    def __review_parameters(self):
        spec = getfullargspec(self.func)
        args = spec.args[1:]  # avoid count self
        count = countitems(args, spec.kwonlyargs, spec.varargs, spec.varkw)
        for k, v in spec.annotations.items():
            if issubclass(v, sliMessage):
                if self.msg_parameter is not None:
                    raise BadMessageArgument(
                        f"You can only have one single {sliMessage.__name__} argument")
                if k in args and args[0] != k:
                    raise BadMessageArgument(
                        f"{sliMessage.__name__} argument must to be the first no-named args or a kwargs")
                if k in args:
                    self.msg_parameter = True
                else:
                    self.msg_parameter = k
                count -= 1
        self.need_arguments = bool(count)

    def run(self, msg: Message):
        args, kwargs = self.extract_args(msg.text)
        args = args or tuple()
        kwargs = kwargs or dict()
        if not self.need_arguments:
            args = tuple()
            kwargs = dict()
        args, kwargs = self.__add_parameters(args, kwargs, msg)
        return self.func(*args, **kwargs)

    def extract_args(self, txt):
        spl = txt.split(None)
        if spl[0].lower() not in self.names:
            raise NotForMeException()
        if len(self.names) == 1:
            return tuple(spl[1:]), None
        return tuple(spl), None

    def __add_parameters(self, args, kwargs, msg):
        if isinstance(self.msg_parameter, str):
            if self.msg_parameter:
                kwargs[self.msg_parameter] = msg
        elif self.msg_parameter is True:
            args = (msg, ) + args
        return args, kwargs

    @property
    def names(self):
        names = self.__name or [self.func.__name__]
        return tuple(map(str.lower, names))


class CmdRegExp(CmdBot):
    def __init__(self, regex: str | re.Pattern, *args, flags=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = regex
        if isinstance(regex, str):
            self.regex = re.compile(regex, flags=flags)

    def extract_args(*args, **kwargs):
        raise NotImplementedError()


class CmdMatch(CmdRegExp):
    def extract_args(self, txt):
        m = self.regex.match(txt)
        if m is None:
            raise NotForMeException()
        return tuple(m.groups()), m.groupdict()


class CmdSearch(CmdRegExp):
    def extract_args(self, txt):
        m = self.regex.search(txt)
        if not m:
            raise NotForMeException()
        return tuple(m.groups()), m.groupdict()


class CmdFindAll(CmdRegExp):
    def extract_args(self, txt):
        m = tuple(self.regex.findall(txt))
        if len(m) == 0:
            raise NotForMeException()
        return m, None


class CmdDefault(CmdBot):
    def extract_args(self, txt):
        return tuple(txt.strip().split()), None

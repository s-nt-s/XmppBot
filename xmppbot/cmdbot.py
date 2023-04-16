import re
import inspect

from .basebot import Message
from .common import to_tuple

re_sp = re.compile(r"\s+")


class NotForMeException(Exception):
    pass


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
        self.__mark_parameters()
        setattr(func, 'cmd', self)
        return func

    def __mark_parameters(self):
        parameters = inspect.signature(self.func).parameters
        for k, v in parameters.items():
            if v.annotation == Message:
                self.msg_parameter = k

    def run(self, slf, msg: Message):
        args, kvargs = self.extract_args(msg.text)
        args = args or tuple()
        kvargs = kvargs or dict()
        self.__add_parameters(kvargs, msg)
        return self.func(slf, *args, **kvargs)

    def extract_args(self, txt):
        spl = txt.split(None)
        if spl[0].lower() not in self.names:
            raise NotForMeException()
        if len(self.names) == 1:
            return tuple(spl[1:]), None
        return tuple(spl), None

    def __add_parameters(self, kvargs, msg):
        if self.msg_parameter:
            kvargs[self.msg_parameter] = msg

    @property
    def names(self):
        names = self.__name or [self.func.__name__]
        return tuple(map(str.lower, names))


class CmdRegExp(CmdBot):
    def __init__(self, regex: str | re.Pattern, *args, flags=0, **kvargs):
        super().__init__(*args, **kvargs)
        self.regex = regex
        if isinstance(regex, str):
            self.regex = re.compile(regex, flags=flags)

    def extract_args(*args, **kvargs):
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

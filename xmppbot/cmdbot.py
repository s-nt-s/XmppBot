import functools
import re
import inspect

from .basebot import Message
from .common import to_tuple

re_sp = re.compile(r"\s+")


class NotForMeException(Exception):
    pass


class CmdName:
    INDEX = 0

    def __init__(
            self,
            *names: str,
            delay: bool = False,
            users: str | list[str] = None):
        CmdName.INDEX += 1
        self.index = CmdName.INDEX
        self.func = None
        self.delay = delay
        self.users = to_tuple(users)
        self.__name = names
        self.parameters = {k: False for k in (
            "reply_to_user",
            "reply_to_message"
        )}
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

        def wrapper_function(*args, **kvargs):
            return self.__call_func(*args, **kvargs)
        functools.update_wrapper(wrapper_function, func)
        setattr(wrapper_function, 'cmd', self)
        return wrapper_function

    def __mark_parameters(self):
        parameters = inspect.signature(self.func).parameters
        for k in self.parameters.keys():
            if k in parameters:
                self.parameters[k] = True

    def __call_func(self, slf, msg: Message):
        args, kvargs = self.extract_args(msg.text)
        args = args or tuple()
        kvargs = kvargs or dict()
        self.__add_parameters(kvargs, msg)
        return self.func(slf, *args, **kvargs)

    def extract_args(self, txt):
        cmd = txt.split(None, 1)[0].lower()
        if cmd not in self.names:
            raise NotForMeException()
        return tuple(txt.split()), None

    def __add_parameters(self, kvargs, msg):
        if self.parameters['reply_to_user']:
            kvargs['reply_to_user'] = msg.sender
        if self.parameters['reply_to_message']:
            kvargs['reply_to_message'] = msg

    @property
    def names(self):
        names = self.__name or [self.func.__name__]
        return tuple(map(str.lower, names))


class CmdRegExp(CmdName):
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


class CmdDefault(CmdName):
    def extract_args(self, txt):
        return tuple(txt.strip().split()), None

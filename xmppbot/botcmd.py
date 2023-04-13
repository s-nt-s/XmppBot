import functools
import re
import inspect

from .basebot import Message

re_sp = re.compile(r"\s+")

class NotForMeException(Exception):
    pass

class CmdBot:
    INDEX = 0
    def __init__(self, delay:bool=False, users:list[str]=None, name:str=None):
        CmdBot.INDEX += 1
        self.func = None
        self.delay = delay
        self.users = users
        self.index = CmdBot.INDEX
        self.name = None
        self.parameters = {k:False for k in (
            "reply_to_user",
            "reply_to_message"
        )}
        if isinstance(name, str):
            self.name = tuple(name.split())

    def is_for_me(self, msg: Message) -> bool:
        if not callable(self.func):
            raise Exception("func is not callable")
        if not(self.delay) and msg.is_delay:
            return False
        if self.users and msg.sender not in self.users:
            return False
        try:
            self.extract_args(msg.text)
        except NotForMeException:
            return False
        return True
        
    def extract_args(self, txt):
        cmd = txt.split(None, 1)[0].lower()
        if cmd not in self.names:
            raise NotForMeException()
        return tuple(txt.split()), None
    
    def callCache(self, slf, msg: Message):
        args, kvargs = self.extract_args(msg.text)
        args = args or tuple()
        kvargs = kvargs or dict()
        if self.parameters['reply_to_user']:
            kvargs['reply_to_user'] = msg.sender
        if self.parameters['reply_to_message']:
            kvargs['reply_to_message'] = msg
        return self.func(slf, *args, **kvargs)

    def __call__(self, func):
        self.func = func
        parameters = inspect.signature(func).parameters
        for k in self.parameters.keys():
            if k in parameters:
                self.parameters[k] = True
        def wrapper_function(*args, **kvargs):
            return self.callCache(*args, **kvargs)
        functools.update_wrapper(wrapper_function, func)
        setattr(wrapper_function, 'cmd', self)
        return wrapper_function

    @property
    def names(self):
        names = self.name or [self.func.__name__]
        return tuple(map(str.lower, names))

class CmdRegExp(CmdBot):
    def __init__(self, regex:str|re.Pattern, *args, flags=0, **kvargs):
        super().__init__(*args, **kvargs)
        self.regex = regex
        if isinstance(regex, str):
            self.regex = re.compile(regex, flags=flags)

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
        if len(m)==0:
            raise NotForMeException()
        return m, None
    
class CmdDefault(CmdBot):
    def is_for_me(self, msg: Message) -> bool:
        if not callable(self.func):
            raise Exception("func is not callable")
        if not(self.delay) and msg.is_delay:
            return False
        return True
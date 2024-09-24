"""
This module provides a IndentingLogger class
IndentingLogger is not meant to be instantiated.

InentingLogger works only in a single thread workflows.

# Use:

@IndentingLogger.register
def a(n=1):
    return b(n)


@IndentingLogger.register
def b(n=2):
    for _ in range(n):
        c()

@IndentingLogger.register
def c():
    pass


@IndentingLogger.register_hook
def hook(msg):
    # all hooks will be passed the logger message
    if 'Function c returned' in msg:
        print(f'hook activated when c returned')

a(3)

# produces the following output:
> Function a called: with params: ((3,), {})
-+-> Function b called: with params: ((3,), {})
-+--+-> Function c called: with params: ((), {})
-+--+-< Function c returned;

-+--+-> Function c called: with params: ((), {})
-+--+-< Function c returned;

-+--+-> Function c called: with params: ((), {})
-+--+-< Function c returned;

-+-< Function b returned;

< Function a returned;

hook activated when c returned
hook activated when c returned
hook activated when c returned


# viable config options:

IndentingLogger.config.LEVEL = 10
IndentingLogger.config.COLOR = True
IndentingLogger.config.LOG_ARGS = True

# on-of switch
IndentingLogger.activate()
IndentingLogger.deactivate()

"""

from functools import wraps, partial
from . import config
import logging

config = config.Config()
config.LEVEL = 10
config.COLOR = True
config.LOG_ARGS = True

handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
handler.setLevel(config.LEVEL)


def colored_text(text, n: int):

    backgrounds = range(255,231,-1)  # white to black
    n = min(n, len(backgrounds) - 1)  # curbing n
    b = backgrounds[n]  # choosing background color
    if b < 243:
        f = 15  # white for dark backgrounds
    else:
        f = 0  # black for bright foregrounds
    # {config.MESSAGE_COLOR}  # tuż przed {text}
    return f'\x1b[38;5;{f}m\x1b[48;5;{b}m{text}\x1b[0m'
    # return f'\033[38;5;{f}m\033[48;5;{b}m{text}\x1b[0m'  # old version



class IndentationHead(logging.Filter):
    INDENTATION_SIGN = '-+-'
    IN_ARROW = '>'
    OUT_ARROW = '<'
    
    def __init__(self):
        super().__init__()
        self.n_indent = 0
        self.current_arrow = ''
        
        
    # def elongate(self, n=0):
    #     return self.INDENTATION_SIGN * n
        
    def increase(self):
        self.n_indent += 1
    
    def decrease(self):
        self.n_indent = max(0, self.n_indent - 1)
        
    @property
    def indentation_header(self):
        return self.INDENTATION_SIGN * self.n_indent
        
    def filter(self, record):
        msg = record.msg
        msg = self.indentation_header + record.msg
        if config.COLOR:
            msg = colored_text(msg, min(15, self.n_indent))
        record.msg = msg
        return record


class CallableHooks(logging.Filter):
    def __init__(self):
        self.registry = list()

    def add(self, cal):
        if not callable(cal):
            raise TypeError(f'Expected callable. Got type {type(cal)}')
        self.registry.append(cal)

    def filter(self, record):
        for cal in self.registry:
            try:
                cal(record.getMessage())
            except RuntimeError:
                pass
        return record


class IndentingLogger:
    indentation_head = IndentationHead()
    callable_hooks = CallableHooks()
    logger = logging.getLogger('indentation_debug_logger')
    logger.addHandler(handler)
    logger.setLevel(config.LEVEL)
    logger.addFilter(callable_hooks)
    logger.addFilter(indentation_head)
    config = config

    registry = set()
    _active = True
    
    @classmethod
    def activate(cls):
        cls._active = True
        
    @classmethod
    def deactivate(cls):
        cls._active = False

    @classmethod
    def register(cls, arg):
        if callable(arg):
            return cls._decorator(arg)

        elif isinstance(arg, int):
            if not arg in (0, 10, 20, 30, 40, 50):
                raise ValueError('Invalid logging.Level')
            return partial(cls._decorator, level=arg)
        else:
            raise TypeError('MethodMetaLogger.register can not accept type {type(arg)} as argument.')

    @classmethod
    def _decorator(cls, fn, level=10):
        cls.registry.add(fn)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if cls._active:
                call_message = f'Function {fn.__name__} called:'
                if config.LOG_ARGS:
                    call_message +=  f' with params: {args, kwargs}'
                local_indentation = "" # cls.deeper()

                #call_message = local_indentation + ' '.join((cls.IN_ARROW, call_message))
                call_message = ' '.join((IndentationHead.IN_ARROW, call_message))

                cls.log(level, call_message)
                IndentingLogger.indentation_head.increase()


            #final_info = ' '.join((IndentationHead.OUT_ARROW, f'Function {fn.__name__} FAILED;'))
            try:
                result = fn(*args, **kwargs)
                final_info = ' '.join((IndentationHead.OUT_ARROW, f'Function {fn.__name__} returned;'))
            except Exception as e:
                final_info = ' '.join((IndentationHead.OUT_ARROW, f'Function {fn.__name__} FAILED;'))
                print('!')
                raise e
            finally:
                if cls._active:
                    #final_info = local_indentation + final_info + '\n'
                    final_info = final_info + '\n'
                    IndentingLogger.indentation_head.decrease()
                    cls.log(level, final_info)

            return result

        return wrapper
    
    @classmethod
    def log(cls, level, message):
        if not isinstance(level, int):
            raise TypeError('level must be type int')
        if not level in (0, 10, 20, 30, 40, 50):
                raise ValueError('Invalid logging.Level')
        if not isinstance(message, str):
            raise TypeError('message must be type str')
        IndentingLogger.logger.log(level, message)

    @classmethod
    def register_hook(cls, cal):
        """
        Registers callables that will be called with the message
        Hooks activity does not alter the message.
        """
        if not callable(cal):
            raise TypeError(f'Expected callable. Got type {type(cal)}')
        cls.callable_hooks.add(cal)


register_indent_logger = register_metalog = IndentingLogger.register
indentating_logger = metalog_logger = IndentingLogger.logger
indentation_head = meta_indentation_head = IndentingLogger.indentation_head

MetodMetaLogger = IndentingLogger  # alias for compatibility

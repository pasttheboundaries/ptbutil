from functools import wraps, partial
from sys import stdout
from . import config
from types import MethodType
import logging
from .loggingmanager import GlobalLoggerManager

config = config.Config()
config.LEVEL = 10

handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
handler.setLevel(config.LEVEL)
#logger = logging.getLogger('meta')
#logger.addHandler(handler)
#logger.setLevel(config.LEVEL)
#GlobalLoggerManager.add(logger)


def colored_text(text, n: int):
    backgrounds = range(255,231,-1)
    n = min(n, len(backgrounds) - 1)
    b = backgrounds[n]
    if b < 243:
        f = 15
    else:
        f = 0
    return f'\033[38;5;{f}m\033[48;5;{b}m{config.MESSAGE_COLOR }{text}\x1b[0m'


class IndentationHead(logging.Filter):
    INDENTATION_SIGN = '-+-'
    IN_ARROW = '>'
    OUT_ARROW = '<'
    
    def __init__(self):
        super().__init__()
        self.n_indent = 0
        self.current_arrow = ''
        
        
    def elongate(self, n=0):
        return self.INDENTATION_SIGN * n
        
    def increase(self):
        self.n_indent += 1
    
    def decrease(self):
        self.n_indent = max(0, self.n_indent - 1)
        
    @property
    def indentation_header(self):
        return self.elongate(self.n_indent)
        
    def filter(self, record):
        record.msg = colored_text(f'{self.indentation_header + record.msg}', self.n_indent)
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


class MetaLogger:
    indentation_head = IndentationHead()
    callable_hooks = CallableHooks()
    logger = logging.getLogger('meta')
    logger.addHandler(handler)
    logger.setLevel(config.LEVEL)
    logger.addFilter(callable_hooks)
    logger.addFilter(indentation_head)
    GlobalLoggerManager.add(logger)


class MethodMetaLogger(MetaLogger):
    registry = set()
    _active = True
    current_indentation = ''
    INDENTATION_SIGN = '-+-'
    IN_ARROW = '>'
    OUT_ARROW = '<'


    @classmethod
    def deeper(cls):
        cls.current_indentation = cls.current_indentation + cls.INDENTATION_SIGN
        return cls.current_indentation
    
    @classmethod
    def shallower(cls):
        if len(cls.current_indentation) > 0:
            cls.current_indentation = cls.current_indentation[:-1]
        else:
            pass
        return cls.current_indentation
    
    @classmethod
    def activate(cls):
        cls._active = True
        
    @classmethod
    def deactivate(cls):
        cls._active = False

    @classmethod
    def register(cls, arg):
        if callable(arg):
            return MethodMetaLogger.decorator(arg)

        elif isinstance(arg, int):
            if not arg in (0, 10, 20, 30, 40, 50):
                raise ValueError('Invalid logging.Level')
            return partial(MethodMetaLogger.decorator, level=arg)
        else:
            raise TypeError('MethodMetaLogger.register can not accept type {type(arg)} as argument.')

    @classmethod
    def decorator(cls, fn, level=10):
        cls.registry.add(fn)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if cls._active:
                call_message = f'Function {fn.__name__} called:'
                if config.LOG_PARAMS:
                    call_message +=  f' with params: {args, kwargs}'
                local_indentation = "" # cls.deeper()
                MethodMetaLogger.indentation_head.increase()
                #call_message = local_indentation + ' '.join((cls.IN_ARROW, call_message))
                call_message = ' '.join((cls.IN_ARROW, call_message))
                cls.log(level, call_message)
            
            try:
                result = fn(*args, **kwargs)
                final_info = ' '.join((cls.OUT_ARROW, f'Function {fn.__name__} returned;'))
            except Exception as e:
                final_info = ' '.join((cls.OUT_ARROW, f'Function {fn.__name__} FAILED;'))
                raise e
            finally:
                if cls._active:
                    
                    #final_info = local_indentation + final_info + '\n'
                    final_info = final_info + '\n'
                    cls.log(level, final_info)
                    MethodMetaLogger.indentation_head.decrease()
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
        MethodMetaLogger.logger.log(level, message)

    @classmethod
    def register_hook(cls, cal):
        """
        registers callables that will bwe called with the message
        """
        if not callable(cal):
            raise TypeError(f'Expected callable. Got type {type(cal)}')
        cls.callable_hooks.add(cal)


register_metalog = MethodMetaLogger.register
metalog_logger = MethodMetaLogger.logger 
meta_indentation_head = MethodMetaLogger.indentation_head

"""
This module misses the point
It is counteradvised to use it
"""


import logging


class GlobalLoggerManager:
    loggers = dict()
    
    @classmethod
    def add(cls, logger):
        if not isinstance(logger, logging.Logger):
            raise TypeError('LoggingManager can only manage logging.Logger')
        cls.loggers[logger.name] = logger
        
    @classmethod    
    def set_level(cls, level):
        for logger_name, logger in cls.loggers.items():
            #logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
                
    @classmethod   
    def critical(cls):
        cls.set_level(logging.CRITICAL)
        
    @classmethod   
    def error(cls):
        cls.set_level(logging.ERROR)
        
    @classmethod   
    def warning(cls):
        cls.set_level(logging.WARNING)
        
    @classmethod   
    def info(cls):
        cls.set_level(logging.INFO)
        
    
    @classmethod   
    def debug(cls):
        cls.set_level(logging.DEBUG)

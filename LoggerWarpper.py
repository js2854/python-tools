#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# Author: JiaSongsong
# Date: 2018-06-15
#
# A logger warpper support specifies to skip frames


import sys
import os.path
import logging


class LoggerWarpper(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        logging.Logger.__init__(self, name, level)
        self._logger_file = logging.__file__.replace('.pyc', '.py')

    def findCaller(self, skip_frame=0):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        # skip findCaller and _log function
        f = sys._getframe(2)
        rv = "(unknown file)", 0, "(unknown function)"
        while f and hasattr(f, "f_code"):
            co = f.f_code
            if co.co_filename == self._logger_file:
                f = f.f_back
                continue
            if skip_frame > 0:
                skip_frame -= 1
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        return rv

    def _log(self, level, msg, args, exc_info=None, extra=None, skip_frame=0):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        try:
            fn, lno, func = self.findCaller(skip_frame)
        except ValueError:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args, exc_info, func, extra)
        self.handle(record)


def log_real_line(fmt, *args, **kwargs):
    kwargs = dict(kwargs, skip_frame=1)
    logger.info(fmt, *args, **kwargs)


def log_func_line(fmt, *args, **kwargs):
    logger.info(fmt, *args, **kwargs)


if __name__ == '__main__':
    logging.setLoggerClass(LoggerWarpper)
    fmt = '%(asctime)s[Thread:%(thread)04d] %(message)s -- [%(levelname)s][%(filename)s:%(lineno)d]'
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt)
    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(formatter)
    logger.addHandler(screen_handler)

    log_func_line('log_func_line')
    log_real_line('log_real_line')

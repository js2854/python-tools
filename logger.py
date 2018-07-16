#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'JiaSong'

import os
import logging
from logging.handlers import RotatingFileHandler
import traceback
import inspect

logger = None


def _cur_dir():
    return os.path.split(os.path.realpath(__file__))[0] + os.path.sep


def _get_logger():
    global logger
    if not logger:
        logger = logging.getLogger("RobotFramework")
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s -- [%(filename)s:%(lineno)d]')

        logfile = _cur_dir() + 'log/RobotFramework.log'
        dirpath = os.path.dirname(logfile)
        os.path.exists(dirpath) or os.makedirs(dirpath)

        file_handler = RotatingFileHandler(logfile, maxBytes=10 << 20, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def get_trace_info(logtrace):
    trace = ''
    if logtrace:
        trace = traceback.format_exc()
        trace = '' if trace.startswith('None') else ('\n' + trace)
    return trace


def _write(msg, level='INFO', also_file=False, logtrace=False):
    exc_str = get_trace_info(logtrace)
    _, filepath, lineno, _, _, _ = inspect.stack()[2]
    filename = os.path.basename(filepath)
    fmt_msg = '{} -- [{}:{}]{}'.format(msg, filename, lineno, exc_str)
    print '*{}* {}'.format(level, fmt_msg)
    if also_file:
        logger = _get_logger()
        level = {
            'TRACE': logging.DEBUG // 2,
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'HTML': logging.INFO,
            'WARN': logging.WARN,
            'ERROR': logging.ERROR
        }[level]
        logger.log(level, fmt_msg)


def trace(msg, also_file=False, logtrace=False):
    _write(msg, 'TRACE', also_file, logtrace)


def debug(msg, also_file=False, logtrace=False):
    _write(msg, 'DEBUG', also_file, logtrace)


def info(msg, also_file=False, logtrace=False):
    _write(msg, 'INFO', also_file, logtrace)


def warn(msg, also_file=False, logtrace=False):
    _write(msg, 'WARN', also_file, logtrace)


def error(msg, also_file=False, logtrace=True):
    _write(msg, 'ERROR', also_file, logtrace)

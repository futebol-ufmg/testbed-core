#!/usr/bin/env python
'''
Logging Module for the CBTM.

This module keeps the global variable 'cbtm_logger' that other modules can
import to use to log their activities. Before this variable can be used, the
init_logger method must be called. This should be done in the main function.
'''

import datetime
import logging

level_dict = {
                "error":logging.ERROR,
                "warning":logging.WARN,
                "info":logging.INFO,
                "debug":logging.DEBUG,
                "notset":logging.NOTSET
                }

def init_logger(level = "info", verbose=False):
    level = level_dict[level]
    cbtm_logger = logging.getLogger("cbtm_logger")
    cbtm_logger.setLevel(level)

    if verbose:
        console = logging.StreamHandler()
        console.setLevel(level)

        c_formatter = logging.Formatter('%(asctime)-15s %(message)s')
        console.setFormatter(c_formatter)

        cbtm_logger.addHandler(console)

    log_dir = '../logs/'
    log_name = datetime.datetime.now().strftime('log_cbtm_%Y_%m_%d')
    log_name = log_dir + log_name

    f_handler = logging.FileHandler(log_name)
    f_handler.setLevel(level)

    f = '%(asctime)-15s %(levelno)s %(threadName)-10s %(funcName)-10s %(message)s'
    f_formatter = logging.Formatter(f)
    f_handler.setFormatter(f_formatter)

    cbtm_logger.addHandler(f_handler)

    strftime = '----------%H:%M:%S----------\n'
    hello_msg = datetime.datetime.now().strftime(strftime)
    sep = '-----------------------------\n'
    hello_msg = sep + hello_msg + sep

    with open(log_name, 'a') as f:
        f.write(hello_msg)

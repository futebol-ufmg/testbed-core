#!/usr/bin/env python
'''
    CBTM"s main module.

    This module defines the main CBTM class.
    To start the CBTM server, just run this module.
'''

import argparse
import threading

from command_handler import CommandHandler
from twisted_server import ConnectionFactory

outlock = threading.Lock()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CBTM Tesbed Manager')
    parser.add_argument('-z', '--zabbix', default=False, action='store_true',
                        help='Select whether to use zabbix as a health monitor or not.')
    parser.add_argument('--log-level', action="store", type=str,
                        choices=["critical", "error", "warning", "info",
                                 "debug", "notset"], default="info",
                        help='Select the log level of the program.')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Select whether to output logs to the console.')
    args = parser.parse_args()

    port = 5006
    handler = CommandHandler(args, port)
    server = ConnectionFactory(handler)

    try:
        server.run_server(port)
    except Exception as e:
        print str(e)
        raise e
    finally:
        server.handler.shutdown()

#!/usr/bin/env python
'''
    CBTM"s main module.

    This module defines the main CBTM class.
    To start the CBTM server, just run this module.
'''

import template_ctrl
import resource_ctrl
import image_ctrl
# import virt
# import os
import subprocess
# import sys
import time
import argparse

import logging
import cbtm_logging
import threading
#from cbtm_logging import get_cbtm_logger
from twisted_server import ConnectionFactory
from response_handler import Handler

from image_ctrl import POOL_PATH

from resource_monitor_cbtm import ResourceMonitorCBTM

outlock = threading.Lock()

class Cbtm(object):
    ''' 
    Main class to define the CBTM.

    The run function of this class will start the CBTM server.

    Attributes:
        log (cbtm_logging): Logging object that is used to create the logs
        usrps (usrp_list): List of the USRPs connected to a VM and their IPs
        handler (response_handler): Function that handles CBTP messages
        server (ConnectionFactory): TCP server that handles requests from the
            clients (most likely the Aggregate Manager)
        port (int): the port which the CBTM server listens to (default 5006)
    '''

    def __init__(self, args):
        #Start the logger
        cbtm_logging.init_logger(level = args.log_level,verbose = args.verbose)
        self.log = logging.getLogger("cbtm_logger")
        self.log.info("Initialized Logger. Log Level: " +
                        str(args.log_level).upper())

        self.log.info('Obtaining available resources')
        self.rm = ResourceMonitorCBTM()
        self.rm.update()
        self.log.info('Resource nodes info:\n' + '\n'.join(
                        map(str,self.rm.get_resources().itervalues())))

        # self.log.info('Opening connections to the hypervisor')
        # conn_list = virt.open_connections()

        self.log.info('Looking up Resources')
        resources = resource_ctrl.check_grid_resources(self.rm.get_resources())
        self.log.debug("Resources Info:\n"+resources.resources_print())

        self.log.debug('Starting Handler')
        self.handler = Handler(self.rm, self.allocate_resource,
                    self.deallocate_resource, self.start_vm, self.shutdown_vm,
                    self.restart_vm, self.make_clean)

        self.log.debug('Starting Connection Factory')
        self.port = 5006
        self.server = ConnectionFactory(self.handler, self.log)


    def run(self):
        '''Start the CBTM server.'''
        self.log.debug('Starting CBTM Server')
        self.server.run_server(self.port)


    def shutdown(self):
        '''Shutdown the CBTM server'''
        self.log.debug('Shuting down CBTM')
        self.handler.shutdown()


    def run_command(self, fullpath, COMMAND):
        result = 'error'
        try:
            ssh = subprocess.Popen(["ssh", "%s" % fullpath, COMMAND],
            shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            result = ssh.stdout.read()
            err = ssh.stderr.read()
            if err:
                self.log.debug('ERROR: '+ str(err))
            # print "Inside run_command"
            # print str(result)
        except Exception as e:
            self.log.debug(str(e))
            return 'error'

        return str(result)


    def delete_user(self, host):
        self.log.debug("=============ENTERING DELETE USER==============")
        user_name = ''

        ip = str(host.get_ip())

        base_user = str(host.get_user())

        fullpath = base_user + '@' + ip

        COMMAND = 'cat /etc/group | grep testbed'
        error_message = 'Unable to retrieve user data, delete user failed.'

        result = self.run_command(fullpath, COMMAND)

        if result:
            user_name = result.rstrip('\n').split(':')[-1]
        else:
            return False

        if user_name:
            COMMAND = 'sudo pkill -u ' + user_name
            #print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False
            
            COMMAND = "docker rm -f $(docker ps -a | tail -n +2" + \
                      " | awk '{print $1}' ) &> /dev/null"

            #print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False

            COMMAND = 'sudo deluser --remove-home ' + user_name
            #print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False

            if 'Done.' in result:
                return True
        else:
            return False


    def ' RETURNING IP: ' + str(node_ip))
            return node_ip
        else:
            return self.make_vm(node, img_type, user, ssh_key, break_flag)


    def clear_image_choice(self,host):

        ip = str(host.get_ip())

        base_user = str(host.get_user())

        fullpath = base_user + '@' + ip

        COMMAND = 'sudo sed -i "s/futebolufmg.\+/ ' + \
        'image_type/g" /opt/docker-wifi/run.sh'
        #print 'running command:', COMMAND
        result = self.run_command(fullpath, COMMAND)
        if 'error' in result:
            return False
        else:
            return True


    def deallocate_resource(self, node):
        host = node.get_host()
        if node.is_raw():
            self.delete_user(host)
            if 'ubuntu' in node.get_default_image():
                self.clear_image_choice(host)
            self.log.debug('Resource %s removed'%host.get_name())
        else:
            self.destroy_vm(node)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CBTM Tesbed Manager')
    parser.add_argument('--log-level', action="store", type=str,
                    choices=[
                                "critical",
                                "error",
                                "warning",
                                "info",
                                "debug",
                                "notset",
                            ],
                    default="info",help='Select the log level of the program.')
    parser.add_argument('--verbose', default=False, action = 'store_true',
                    help='Select whether to output logs to the console.')

    args = parser.parse_args()
    coord = Cbtm(args)
    try:
        coord.run()
    except Exception as e:
        print str(e)
        raise e
    finally:
        coord.shutdown()

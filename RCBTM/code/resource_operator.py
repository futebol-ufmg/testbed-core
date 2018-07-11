# !/usr/bin/env python

import sys
import time
import logging
import threading
import subprocess

import ctrl_utils
import cbtm_logging

from telos_b import TelosB
from container import Container
from raspberry_pi import RaspberryPI
from virtual_machine import VirtualMachine
from openflow_switch import OpenFlowSwitch
from resource_monitor_cbtm import ResourceMonitorCBTM

from resource_list import ResourceList

sys.path.insert(0, "/home/ftbl/RCBTM/code/")
outlock = threading.Lock()


class ResourceOperator(object):

    def __init__(self, args, port):
        cbtm_logging.init_logger(level=args.log_level, verbose=args.verbose)
        self.log = logging.getLogger("cbtm_logger")
        self.log.info("Initialized Logger. Log Level: " +
                      str(args.log_level).upper())
        res_num = 8
	basic_id = 10
        self.vms = VirtualMachine(self.log, 8, 10)
        self.rasps = RaspberryPI(self.log, 16, 40)
        self.telosbs = TelosB(self.log, 16, 70)
        self.switchs = OpenFlowSwitch(self.log, 1, 0)
        self.containers = Container(self.log, 8, 50)

        self.log.info('Obtaining available resources')
        self.rm = ResourceMonitorCBTM()
        self.rm.update()
        self.log.info('Resource nodes info:\n' +
                      '\n'.join(map(str,
                                    self.rm.get_resources().itervalues())))
        self.log.info('Looking up Resources')
        resources = self.check_grid_resources(self.rm.get_resources())
        self.log.debug("Resources Info:\n" + resources.resources_print())
        self.log.debug('Starting Handler')
        self.log.debug('Starting Connection Factory')
        self.port = port

    def identify_resources(self, res_id):
        if(res_id >= 11 and res_id <= 18):
            return "VirtualMachine"
        if(res_id >= 25 and res_id <= 28):
            return "TelosB"
        if(res_id >= 42 and res_id <= 44):
            return "RaspberryPI"
        if(res_id >= 52 and res_id <= 58):
            return "Container"
        return "Invalid"

    def check_grid_resources(self, node_dict):
        ''' 
        Check the availability of the resources (USRP's)

        Args:
            node_dict (dict(str:NodeCBTM)): Dictionary with the nodes available
        Returns:
            usrps (list): list of USRP's in use and the IP of the respective VM
            If the VM is turned off, the ip returned is 0.0.0.0
        '''
        resources = ResourceList(map(str, node_dict.iterkeys()))

        for node in node_dict.itervalues():
            res_id = str(node.get_id())
            host = node.get_host()
            conn = host.get_conn_info()

            if node.is_raw():
                resources.use[res_id] = self.isRawBeingUsed(host)
                resources.ips[res_id] = host.get_ip()
                resources.booted[res_id] = True

            elif conn:
                vm_names = conn.get_all_vms()
                if vm_names == []:
                    continue   # No VMs defined in this rack. Move to next Rack

                for vm in vm_names:
                    # Check if VM is an USRP VM, otherwise skip it
                    #if self.get_vm_name(res_id) not in vm:
                    if self.vms.get_vm_name(res_id) in vm:
                        continue
                    # For each VM, get interfaces IPs
                    ext_ip = conn.get_vm_info(vm)

                    # get USRP id from the (rack, interface) tupple
                    # res_id = vm[9:]
                    resources.use[res_id] = True
                    resources.ips[res_id] = ext_ip
                    try:
                        dom = conn.conn.lookupByName(vm)
                        if dom.isActive():
                            resources.booted[res_id] = True
                    except Exception:
                        raise

        return resources

    def check_resource_status(self, node):
        ''' 
        Checks the status of the RESOURCE: defined, booted and IP.
        '''

        host = node.get_host()
        res_num = str(node.get_id())

        if node.is_raw():
            # base_user = 'pi' if 'rasp' in host.get_name() else 'futebol'

            if self.isRawBeingUsed(host):
                use = True
                booted = True
                ip = host.get_ip()
            else:
                use = False
                booted = False
                ip = '0.0.0.0'
        else:
            try:
                conn_info = host.get_conn_info()
            except Exception:
                host_name = host.get_name()
                print('Could not find connection for the intended rack:',
                      host_name)
                raise

            try:
                dom = conn_info.conn.lookupByName(self.vms.get_vm_name(res_num))
                use = True
            except Exception:
                # self.log.warning("Cloud not find the USRP" + str(usrp_num))
                use = False
                booted = False
                ip = '0.0.0.0'

            if use:
                booted = dom.isActive()
                if booted:
                    ip = conn_info.get_vm_info(self.vms.get_vm_name(res_num))
                else:
                    ip = '0.0.0.0'

        return use, booted, ip

    def run_command(self, fullpath, COMMAND):
        result = 'error'
        try:
            ssh = subprocess.Popen(["ssh", "%s" % fullpath, COMMAND],
                                   shell=False, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

            result = ssh.stdout.read()
            err = ssh.stderr.read()
            if err:
                self.log.debug('ERROR: ' + str(err))
            # print "Inside run_command"
            # print str(result)
        except Exception as e:
            self.log.debug(str(e))
            return 'error'

        return str(result)

    def make_clean(self, non_active_nodes):
        """
        Args:
            non_active_usrps (list): List of NodeCBTM with the resources that
                                     we need to make sure are deleted.
        """
        print 'In make clean:' + str(non_active_nodes)

        for node in non_active_nodes:
            self.log.debug('In make clean for node: ' + str(node))
            self.deallocate_resource(node)

        return "ok"

    def allocate_resource(self, node, img_type, user, ssh_key, break_flag):
        # if img_type == 'raspberry':
        res_id = node.get_id()
        if node.is_raw():
            # print 'allocating raw'
            host = node.get_host()
            node_ip = host.get_ip()
            # print host.get_user()
            # print node_ip
            self.create_user(res_id, user, ssh_key, node_ip, img_type,
                             node.is_raw(), host.get_user())
            self.log.debug('RAW RESOURCE ALLOCATED SUCCESSFULLLY,' +
                           ' RETURNING IP: ' + str(node_ip))
            return node_ip
        else:
            return self.vms.make_vm(node, img_type, user, ssh_key, break_flag)

    def deallocate_resource(self, node):
        host = node.get_host()
        if node.is_raw():
            self.delete_user(host)
            if 'ubuntu' in node.get_default_image():
                self.vms.clear_image_choice(host)
            self.log.debug('Resource %s removed' % host.get_name())
        else:
            self.vms.destroy_vm(node)

    def isRawBeingUsed(self, host):
        fullpath = host.get_user() + "@" + host.get_ip()
        # check if there is any user in group testbed
        COMMAND = 'cat /etc/group | grep testbed'

        ssh = subprocess.Popen(["ssh", "%s" % fullpath, COMMAND], shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

        read = ssh.stdout.read()
        # read_err = ssh.stderr.read()

        result = str(read)[:-1].split(':')[-1]
        print 'RESULT SSH RAW IS BEING USED:', bool(result)

        # if there is a user in group testbed resource is already assigned
        return bool(result)

    # colocar dentro das classes de recursos
    def delete_user(self, host):
        self.log.debug("=============ENTERING DELETE USER==============")
        user_name = ''

        ip = str(host.get_ip())

        base_user = str(host.get_user())

        fullpath = base_user + '@' + ip

        COMMAND = 'cat /etc/group | grep testbed'
        # error_message = 'Unable to retrieve user data, delete user failed.'

        result = self.run_command(fullpath, COMMAND)

        if result:
            user_name = result.rstrip('\n').split(':')[-1]
        else:
            return False

        if user_name:
            COMMAND = 'sudo pkill -u ' + user_name
            # print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False
            COMMAND = "docker rm -f $(docker ps -a | tail -n +2" + \
                      " | awk '{print $1}' ) &> /dev/null"

            # print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False

            COMMAND = 'sudo deluser --remove-home ' + user_name
            # print 'running command:', COMMAND
            result = self.run_command(fullpath, COMMAND)
            if 'error' in result:
                return False

            if 'Done.' in result:
                return True
        else:
            return False

    def create_user(self, res_id, user, ssh_key, ip, img_type, raw, base_user):
        if(self.identify_resources(res_id) == "TelosB"):
            self.telosbs.create_user(user, ssh_key, ip, img_type,
                                     raw, base_user)
        if(self.identify_resources(res_id) == "Container"):
            self.containers.create_user(user, ssh_key, ip,
                                        img_type, raw, base_user)
        if(self.identify_resources(res_id) == "RaspberryPI"):
            self.rasps.create_user(user, ssh_key, ip, img_type,
                                   raw, base_user)
        if(self.identify_resources(res_id) == "VirtualMachine"):
            self.vms.create_user(user, ssh_key, ip, img_type,
                                 raw, base_user)
        if(self.identify_resources(res_id) == "OpenFlowSwitch"):
            self.switchs.create_user(user, ssh_key, ip,
                                     img_type, raw, base_user)


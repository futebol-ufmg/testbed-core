# !/usr/bin/env python

from __future__ import absolute_import

import logging
import threading
import cbtm_logging

from resource_list import ResourceList
from resource_monitor_cbtm import ResourceMonitorCBTM
from testbed_modules.resource_utils.src.cbtm_resource import CBTM_Resource


outlock = threading.Lock()


class ResourceOperator(object):

    def __init__(self, args, port):
        cbtm_logging.init_logger(level=args.log_level, verbose=args.verbose)
        self.log = logging.getLogger("cbtm_logger")
        self.log.info("Initialized Logger. Log Level: " +
                      str(args.log_level).upper())

        self.log.info('Obtaining available resources')
        self.rm = ResourceMonitorCBTM()
        self.rm.update()
        self.log.info('Resource nodes info:\n' +
                      '\n'.join(map(str,
                                    self.rm.get_resources().itervalues())))
        self.log.info('Looking up Resources')
        resources = self.check_grid_resources(self.rm.get_resources())
        # Get a list of available resources from Zabbix and make a list
        # of resource objects based on the response
        self.log.debug("Resources Info:\n" + resources.resources_print())
        self.log.debug('Starting Handler')
        self.log.debug('Starting Connection Factory')
        self.port = port

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
            resource = CBTM_Resource.factory(self.log, node)
            use, booted, ip = resource.get_resource_info()
            if (use is None) or (booted is None) or (ip is None):
                continue
            else:
                resources.use[res_id] = use
                resources.booted[res_id] = booted
                resources.ips[res_id] = ip
            # if node.is_raw():
            #     resources.use[res_id] = self.isRawBeingUsed(host)
            #     resources.ips[res_id] = host.get_ip()
            #     resources.booted[res_id] = True

            # elif conn:
            #     vm_names = conn.get_all_vms()
            #     if vm_names == []:
            #         continue   # No VMs defined in this rack. Move to next Rack

            #     for vm in vm_names:
            #         # Check if VM is an USRP VM, otherwise skip it
            #         #if self.get_vm_name(res_id) not in vm:
            #         if self.vms.get_vm_name(res_id) in vm:
            #             continue
            #         # For each VM, get interfaces IPs
            #         ext_ip = conn.get_vm_info(vm)

            #         # get USRP id from the (rack, interface) tupple
            #         # res_id = vm[9:]
            #         resources.use[res_id] = True
            #         resources.ips[res_id] = ext_ip
            #         try:
            #             dom = conn.conn.lookupByName(vm)
            #             if dom.isActive():
            #                 resources.booted[res_id] = True
            #         except Exception:
            #             raise

        return resources

    def check_resource_status(self, node):
        '''
        Checks the status of the RESOURCE: defined, booted and IP.
        '''

        resource = CBTM_Resource.factory(self.log, node)
        use, booted, ip = resource.get_status()
        return use, booted, ip

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
        # TODO: MAKE RESOURCE
        resource = CBTM_Resource.factory(self.log, node)
        # TODO: CALL ALLOCATE ON RESOURCE
        resource.allocate(user, ssh_key, img_type, break_flag)

    def deallocate_resource(self, node):
        """ Deallocate a resource on a given node object.
        Arguments:
            node {NodeCBTM} -- Node object containing information about node.
        """
        resource = CBTM_Resource.factory(self.log, node)
        resource.deallocate()

    def start_resource(self, node):
        resource = CBTM_Resource.factory(self.log, node)
        resource.start()

    def shutdown_resource(self, node):
        resource = CBTM_Resource.factory(self.log, node)
        resource.shutdown()

    def restart_resource(self, node):
        resource = CBTM_Resource.factory(self.log, node)
        resource.restart()


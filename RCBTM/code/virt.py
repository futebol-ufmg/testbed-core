#!/usr/bin/env python
'''
    Virt Module

    Provides some generic functions to manage connections to Hypervisors and to
    retrive general information about the VM's, like Name and IP Address.
'''

import sys
import logging
import libvirt
import xml.etree.ElementTree as ET
from isc_dhcp_leases import IscDhcpLeases
from testbed_modules.resource_utils.src.ctrl_utils import POOL_NAME


DHCP_LEASES_PATH = '/var/lib/dhcp/dhcpd.leases'


class ConnInfo():
    '''
    Class to store an individual libvirt connection and helper functions.

    Attributes:
        host_name (string): Name of the Rack
        conn_uri (string): URI of the connection
        conn (dict): Libvirt connection to a rack
    '''

    def __init__(self, host_name, conn_uri):
        self.host_name = host_name
        self.conn_uri = conn_uri
        self.conn = self.open_connection(conn_uri)
        self.log = logging.getLogger("cbtm_logger")

    def open_connection(self, uri_str):
        '''
        Helper function to open a libvirt connection.
        Used for conviniece (avoids testing if the connection was opened every
        single time).

        Args:
            uri_str (string): String that defines the URI of the connection.
                Example: 'qemu+ssh:/user@node/session'

        Returns:
            conn (libvirt.virConnect): Libvirt connection to the hypervisor

        Raises:
            SystemExit: An error occurred opening the connection
                and the program will be terminated.
        '''
        conn = libvirt.open(uri_str)
        if conn is None:
            sys.exit('Failed to open connection to ' + uri_str)
        return conn

    def get_host_name(self):
        '''
        Get the name of the Host

        Returns:
            Host_name (string)
        '''
        return self.host_name

    def get_all_vms(self):
        '''
        Get the names of all defined (turn on or off) VMs

        Returns:
            domain_names (list): List of domain names
        '''
        domain_names = self.conn.listDefinedDomains()
        domain_ids = self.conn.listDomainsID()
        if domain_ids is not None:
            for domain_id in domain_ids:
                domain = self.conn.lookupByID(domain_id)
                domain_names.append(domain.name())
        return domain_names

    def get_all_vols(self):
        '''
        Get the names of all defined volumes in the CBTM pool

        Returns:
            volume_names (list): List of volume names
        '''
        poolName = POOL_NAME
        sp = self.conn.storagePoolLookupByName(poolName)
        if sp is None:
            self.log.debug('Failed to find storage pool ' + poolName)
            return -1

        stgvols = sp.listVolumes()
        return stgvols

    def get_vm_info(self, dom_name):
        '''
        Get the IP info of interfaces on the VM

        Args:
            dom_name (string): name of the desired domain

        Returns:
            eth0_ip, usrp_if (string): eth0 and USRP interface
        '''
        # Get XML description of domain

        dom = self.conn.lookupByName(dom_name)
        dom_xml = dom.XMLDesc(0)
        root = ET.fromstring(dom_xml)

        # Find MAC address of the VMs primary interface
        for if_element in root.iter('interface'):
            if if_element.attrib['type'] == 'bridge' and if_element.find('virtualport') is None:
                outbound_if = if_element.find('mac').attrib['address']

        # Find what is the IP of the bridged interface. This only makes sense
        # if the VM is turned on. It will return 0.0.0.0 if the VM is off. This
        # will use QEMU Agent. Need to modify the XML of the VM's to access it
        # and install qemu-guest-agent on them.
        if dom is None:
            self.log.debug('Failed to get the domain object')

        out_ip = '0.0.0.0'
        try:
            ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)

            self.log.debug("The interface IP addresses:")
            for name, val in ifaces.iteritems():
                if val['addrs']:
                    for ipaddr in val['addrs']:
                        if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            self.log.debug("iface name: " + str(name) +
                                           "  Addr:  " + ipaddr['addr'] +
                                           " VIR_IP_ADDR_TYPE_IPV4")
                            if '192.168.0' in ipaddr['addr']:
                                out_ip = ipaddr['addr']
                                return out_ip
                        elif ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV6:
                            self.log.debug("iface name: " + str(name) +
                                           "  Addr:  " + ipaddr['addr'] +
                                           " VIR_IP_ADDR_TYPE_IPV6")
        except Exception as e:
            self.log.debug("ERROR trying to obtain VM IP: " + str(e))
            self.log.debug('repr(e):  ' + str(repr(e)))
        # Find out the IP by collecting the MAC address and searching
        # for it on the DHCP
        interfaces = []
        if dom.isActive():
            try:
                leases = IscDhcpLeases(DHCP_LEASES_PATH)
                vm_lease = leases.get_current()[outbound_if]
                out_ip = vm_lease.ip
            except Exception:
                self.log.debug("Could not get IP of VM: " + str(dom_name))
        return out_ip

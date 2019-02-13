import json
from hostcbtm import HostCBTM
from nodecbtm import NodeCBTM
from resource_monitor import ResourceMonitor
import testbed_modules.DBHandler.src.user_resources as u_res
from testbed_modules.DBHandler.src.DBConnection import DBConnection
from testbed_modules.health_server.zabbix.zabbix_monitor import ZabbixMonitor


class ZabbixMonitorCBTM(ResourceMonitor):

    def __init__(self, verbose=False):
        self.dbconn = DBConnection(u_res.db_host,
                                   'root',
                                   u_res.db_passwd,
                                   'testbd')
        # Frontend objects
        self.host_dict = {}
        self.resources = {}
        # Internal objects
        self.complete_host_dict = {}
        self.all_resources = {}
        # Zabbix object
        self.zabbix_monitor = ZabbixMonitor(verbose=verbose)
        # Verbose option
        self.verbose = verbose

    def __update_complete_lists(self):
        if self.verbose:
            print('start update complete list')
        slivers, result = self.dbconn.get_all_slivers()
        self.slivers = {}
        for sliverid, hardware, slivertype in slivers:
            self.slivers[int(sliverid)] = \
                {'hardware': hardware,
                 'raw': True if 'raw' in slivertype else False,
                 'default_image': self.dbconn.get_default_image(sliver_id=sliverid)[0],
                 'images': self.dbconn.get_sliver_images(sliver_id=sliverid)[0],
                 }
        if self.verbose:
            print('Finish getting sliver information: ', self.slivers)
        equipment_info, result = \
            self.dbconn.get_equipment_info_control_network()
        if equipment_info == -1:
            print('ERROR: empty control_network_hosts on ResourceMonitorCBTM' +
                  ' Zabbix Version')
        all_resources = {}
        for rid, slid, hostname, host_ip, host_user in equipment_info:
            node_usb, result = self.dbconn.get_resource_usb(rid)

            try:
                host_obj = self.complete_host_dict[hostname]
            except Exception:
                self.complete_host_dict[hostname] = {'hostname': hostname,
                                                     'ip': host_ip,
                                                     'user': host_user}
                # self.host_dict[hostname] = HostCBTM(hostname,
                #                                     host_ip,
                #                                     host_user)
            finally:
                host_obj = self.complete_host_dict[hostname]
            all_resources[int(rid)] = \
                {'id': int(rid),
                 'hardware': self.slivers[slid]['hardware'],
                 'default_image': self.slivers[slid]['default_image'],
                 'images': self.slivers[slid]['images'],
                 'usb': node_usb,
                 'raw': self.slivers[slid]['raw'],
                 'host': host_obj}
            # all_resources[int(rid)] = \
            #     NodeCBTM(int(rid),
            #              self.slivers[slid]['hardware'],
            #              self.slivers[slid]['default_image'],
            #              self.slivers[slid]['images'],
            #              node_usb,
            #              self.slivers[slid]['raw'],
            #              host_obj)
        self.all_resources = all_resources
        print('finish update __update_complete_lists')

    def update(self):
        if self.verbose:
            print('Start updates')
        self.__update_complete_lists()
        # self.zabbix_monitor.get_available_resources()
        resources = {}
        host_dict = {}
        for rid in self.zabbix_monitor.get_available_resources():
            host = self.all_resources[rid]['host']
            host_dict[host['hostname']] = HostCBTM(host['hostname'],
                                                   host['ip'],
                                                   host['user'])
            resources[rid] = NodeCBTM(int(rid),
                                      self.all_resources[rid]['hardware'],
                                      self.all_resources[rid]['default_image'],
                                      self.all_resources[rid]['images'],
                                      self.all_resources[rid]['usb'],
                                      self.all_resources[rid]['raw'],
                                      host_dict[host['hostname']])
        self.host_dict = host_dict
        self.resources = resources
        if self.verbose:
            print('all_resources', self.all_resources, '\n\n')
            print('complete host_dict', self.complete_host_dict, '\n\n')
            print('slivers: ', self.slivers, '\n\n')
            print('resources', self.resources, '\n\n')
            print('complete host_dict', self.host_dict, '\n\n')

    def get_hosts(self):
        return self.host_dict

    def get_resource(self, node_id):
        try:
            return self.resources[int(node_id)]
        except Exception:
            print('Resource not found')
            return None


if __name__ == '__main__':
    try:
        rm = ZabbixMonitorCBTM(verbose=True)
        # while True:
        #     request = ''
        #     request = raw_input('Enter request: ')
        #     rm.request = 'HM:' + request
        msg = rm.update()

        # print(str(rm.get_resources()))
        # print(map(str, rm.get_resources().iterkeys()))
        # print(map(str, rm.get_resources().itervalues()))
    except KeyboardInterrupt:
        print('\nFinishing')
    except Exception as e:
        print('ERROR: ' + str(e))


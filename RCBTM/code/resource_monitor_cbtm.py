import json
from resource_monitor import ResourceMonitor
from hostcbtm import HostCBTM
from nodecbtm import NodeCBTM


class ResourceMonitorCBTM(ResourceMonitor):

    def __init__(self):
        super(ResourceMonitor, self).__init__()
        self.host = '127.0.0.1'
        # Frontend IP
        self.port = 4000
        self.request = 'CB:gr'
        self.host_dict = {}
        self.resources = {}

    def _decode(self, hosts):
        resources = {}
        try:
            for name, host in hosts.iteritems():

                nodes = host['nodes']
                for node in nodes:
                    resources[int(node['id'])] = NodeCBTM(
                        node['id'],
                        node['hardware'],
                        node['default_image'],
                        node['images'],
                        node['usb'],
                        node['raw'],
                        self.host_dict[name])
        except Exception as e:
            print('Raise inside _decode of resource_monitor_cbtm')
            raise e
        finally:
            self.resources = resources

    def _update_host_dict(self, hosts):
        old_hosts = [h for h in self.host_dict.iterkeys()]
        new_hosts = [h for h in hosts.iterkeys()]

        added_racks = list(set(new_hosts) - set(old_hosts))
        removed_racks = list(set(old_hosts) - set(new_hosts))

        new_host_dict = {name: host
                         for name, host in self.host_dict.iteritems()
                         if name not in removed_racks}

        for name in added_racks:
            new_host_dict[name] = HostCBTM(name, hosts[name]['ip'],
                                           hosts[name]['user'])

        self.host_dict = new_host_dict

    def update(self):
        try:
            msg = self.send_health_request(self.request)
            hosts = json.loads(msg)
            self._update_host_dict(hosts)
            self._decode(hosts)
        except Exception as e:
            print('ERROR-ResourceMonitorCBTM: ' + str(e))

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
        rm = ResourceMonitorCBTM()
        while True:
            request = ''
            request = raw_input('Enter request: ')
            rm.request = 'HM:' + request
            msg = rm.update()

            print(str(rm.get_resources()))
            print(map(str, rm.get_resources().iterkeys()))
            print(map(str, rm.get_resources().itervalues()))
    except KeyboardInterrupt:
        print('\nFinishing')
    except Exception as e:
        print('ERROR: ' + str(e))

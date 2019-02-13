class ResourceList(object):
    '''
    Class that holds a list of USRP parameters. This class

    Attributes:
        use (dict): Dictionary that holds an Bool for each USRP.
            These bools are used to check if an USRP is in use or not.
        ips (dict): A dictionary class that holds the VM's IPs
            of each USRP.
    '''

    def __init__(self, resources):
        self.use = {}
        self.booted = {}
        self.ips = {}

        for key in resources:
            self.use[key] = False
            self.booted[key] = False
            self.ips[key] = '0.0.0.0'

    def resources_print(self):
        res_str = 'RESOURCE ID  DEFINED  BOOT    IP'
        for res in self.use.keys():
            res_str += '\n        ' + str(res) + '    ' + str(self.use[res]) + \
                    '    ' + str(self.booted[res]) + '    ' + self.ips[res]
        return res_str


import subprocess
from virt import ConnInfo
from host import Host

class HostCBTM(Host):
    
    def __init__(self, name, ip, user):
        super(HostCBTM, self).__init__(name,ip,user)
        self.conn_info = None
        if 'rasp' not in self.get_name():
            self._open_connection()


    def _open_connection(self):

        fullpath = self.get_user()+'@'+ self.get_ip()
        uri = 'qemu+ssh://' + fullpath +'/system'

        ssh = subprocess.Popen(['ssh', '-t ', fullpath, 'uhd_find_devices'],
            shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out = ssh.stdout.read()
        err = ssh.stderr.read()

        self.conn_info = ConnInfo(self.get_name(),uri)

    def get_conn_info(self):
        return self.conn_info


import time
import threading
import subprocess
import ctrl_utils

from resource import Resource

outlock = threading.Lock()

class VirtualMachine(Resource):
    def __init__(self, log, res_num, basic_id):
        super(VirtualMachine, self).__init__(log, res_num, basic_id)
        #self.log = log
        #self.log.debug("Creating VirtualMachine Object\n")

    def get_vm(self, node):
        '''
        Get VM name from an USRP Id, if the USRP is attached to a VM.

        Args:
            node (NodeCBTM): Resource
        Returns:
            vm_name (string): if such VM exists, -1 if the VM is not found
        '''
        host = node.get_host()
        res_num = node.get_id()

        conn = host.get_conn_info()

        vm_names = conn.get_all_vms()
        result = -1

        expected_name = self.get_vm_name(res_num)
        if vm_names != []:
            for vm in vm_names:
                if vm == expected_name:
                    result = vm
        else:
            result = -1
        return result

    def get_vm_name(self, node):
        # comentario
        return 'basic_eu_' + str(node)

    def make_vm(self, node, img_type, user, ssh_key, break_flag):
        '''
        Create a new VM to be used with a USRP.

        Args:
            node (NodeCBTM): Node to be used
            img_type (string): Type of image to be used
            user (string): User for the VM
            ssh_key (string): SSH key for the user
        '''
        try:
            host = node.get_host()
            res_num = str(node.get_id())

            self.log.debug('Creating VM image. (This may take a while).')
            self.log.debug('Resource ' + str(res_num))

            if img_type not in node.get_images():
                self.log.warning('Unrecognized image type:' + str(img_type) +
                                 ' Getting plain image instead')
                img_type = node.get_default_image()

            ctrl_utils.copy_image('master-' + img_type, 'basic_eu_' +
                                  res_num, host)

            img_name = 'basic_eu_' + res_num + '.img'

            vm_xml = ctrl_utils.create_xml(node, ctrl_utils.POOL_PATH +
                                           img_name, img_type)
            self.log.debug("##### InsertLinkInVm #####")
            # vm_xml = cbtm_links.insertLinkInVm(res_num, vm_xml)
            # Alter xml to vxlan
            ctrl_utils.define_and_boot_vm(host, vm_xml)
            self.log.debug('VM Defined and Booting.')
            # The VM takes some time to boot,
            # wait a few seconds before asking for the IP
            out_ip = '0.0.0.0'
            boot_time = 30      # Give the VM some time to boot.
            check_interval = 0.5
            time.sleep(boot_time)
            time0 = time.time()
            self.log.debug("Starting to get IP")
            while out_ip == '0.0.0.0':
                out_ip = host.get_conn_info().get_vm_info('basic_eu_' +
                                                          res_num)
                if time.time() - time0 > 240:
                    out_ip = '0.0.0.0'
                    break
                time.sleep(check_interval)
            if out_ip != '0.0.0.0':
                self.create_user(user, ssh_key, out_ip, img_type,
                                 node.is_raw(), 'cbtm')
            return out_ip

        except RuntimeError as e:
            self.log.debug(str(e))
            return

    def destroy_vm(self, node):
        """
            Delete a VM

            Args:
                node (NodeCBTM): RESOURCE to be used
        """
        if node.is_raw():
            return

        host = node.get_host()
        # res_num = node.get_id()

        vm_name = self.get_vm(node)
        if vm_name != -1:
            self.log.debug("Deleting: " + str(vm_name))
            ctrl_utils.destroy_vm(host, vm_name)
        vol_name = self.get_vol(node)
        if vol_name != -1:
            vol_name = vol_name.split('.')[0]
            self.log.debug("Deleting: " + str(vol_name))
            ctrl_utils.del_image(vol_name, host)

    def start_vm(self, node):
        """
        Args:
            node (NodeCBTM): RESOURCE to be used
        """
        if node.is_raw():
            return

        host = node.get_host()
        res_num = node.get_id()
        vm_name = self.get_vm(node)

        if vm_name == -1:
            self.log.debug('No VM found for Resource %s' % res_num)
        else:
            self.log.debug('Starting VM %s' % vm_name)
            ctrl_utils.start_vm(host, vm_name)

    def shutdown_vm(self, node):
        """
           Args:
                node (NodeCBTM): RESOURCE to be used
        """
        if node.is_raw():
            return

        host = node.get_host()
        res_num = node.get_id()
        vm_name = ctrl_utils.get_vm(node)

        if vm_name == -1:
            self.log.debug('No VM found for USRP %s' % res_num)
        else:
            self.log.debug('Shutting Down VM %s' % vm_name)
            ctrl_utils.shutdown_vm(host, vm_name)

    def restart_vm(self, node):
        """
        Args:
            node (NodeCBTM): RESOURCE to be used
        """
        if node.is_raw():
            return

        host = node.get_host()
        res_num = node.get_id()
        vm_name = self.get_vm(node)

        if vm_name == -1:
            self.log.debug('No VM found for USRP %s' % res_num)
        else:
            self.log.debug('Restarting VM %s' % vm_name)
            ctrl_utils.restart_vm(host, vm_name)

    def get_vol(self, node):
        '''
        Get Volume name from an USRP Id, if the volume exists.

        Args:
            conn_list (ConnInfo): Dictionary of Libvirt connections to the
            Racks usrp_num (int): USRP Id
        Returns:
            vol_name (string): Volume name if volume exists, -1 if it doesn't.
        '''

        host = node.get_host()
        res_num = node.get_id()
        conn = host.get_conn_info()

        img_name = self.get_vm_name(res_num) + '.img'

        vol_names = conn.get_all_vols()
        if img_name in vol_names:
            return img_name
        else:
            return -1

    def clear_image_choice(self, host):
        ip = str(host.get_ip())

        base_user = str(host.get_user())

        fullpath = base_user + '@' + ip

        COMMAND = 'sudo sed -i "s/futebolufmg.\+/ ' + \
                  'image_type/g" /opt/docker-wifi/run.sh'
        # print 'running command:', COMMAND
        result = self.run_command(fullpath, COMMAND)
        if 'error' in result:
            return False
        else:
            return True

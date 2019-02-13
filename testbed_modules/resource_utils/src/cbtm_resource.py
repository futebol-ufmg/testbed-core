import time
import threading
import subprocess
import ctrl_utils
from resource import Resource

# from node import Node

outlock = threading.Lock()


class CBTM_Resource(Resource):
    """ This class implements a Resource for the CBTM.

    A Resource is an available Node (available meaning functioning)
    The CBTM_Resource contains some peculiarities not shared
    with any other software, for example, code related to admin tasks
    on hosts and nodes such as create_user.

    Extends:
        Resource
    """
    def __init__(self, log, node):
        super(CBTM_Resource, self).__init__(node.get_id(), 'cbtm_resource')
        self.log = log
        self.node = node

    # The following code implements the Factory Method design pattern
    def factory(log, node):
        if node.get_id() >= 90:
            return OpenSTF(log, node)
        if node.get_id() >= 80:
            return VirtualMachine(log, node)
        if node.get_id() > 60:
            return TelosB(log, node)
        if node.get_id() > 50:
            return Container(log, node)
        if node.get_id() > 30:
            return RaspberryPI(log, node)
        if node.get_id() > 10:
            return VirtualMachine(log, node)
        else:
            return OpenFlowSwitch(log, node)

    factory = staticmethod(factory)
    # End of Factory Method design pattern code

    def create_user(self, user, ssh_key, ip, img_type, raw, base_user):
        """
            @brief      Creates an user in a machine (virtual or raw).
            @param      self       The object
            @param      user       The user
            @param      ssh_key    The ssh key for the user
            @param      ip         The IP of the machine
            @param      img_type   The image type of the allocation
            @param      raw        True if machine is raw, False otherwise
            @param      base_user  The base user for the machine
            @return     No return value is set in the function.
        """
        self.log.debug('Creating user for usage in the RESOURCE')
        self.log.debug('Received IP:   ' + str(ip))
        self.log.debug('PARAMETERS: ' + str(user) + ' ' + str(ssh_key) + ' ' +
                       str(ip) + ' ' + str(img_type) + ' ' + str(raw) + ' ' +
                       str(base_user))

        COMMAND = 'echo "${USER}:userpass::::/home/${USER}:/bin/bash"' + \
                  ' >> user.txt' + \
                  ' && sudo -S newusers user.txt' + \
                  ' && rm user.txt' + \
                  ' && sudo mkdir -p /home/${USER}/.ssh' + \
                  ' && sudo echo "${SSH_KEY}" >> authorized_keys' + \
                  ' && sudo echo "ServerAliveInterval 60" >> config' + \
                  ' && sudo mv authorized_keys /home/${USER}/.ssh' + \
                  ' && sudo mv config /home/${USER}/.ssh' + \
                  ' && sudo chown ${USER}:${USER} /home/${USER}/.ssh -R'

        HOST = base_user + '@' + ip
        if raw:
            COMMAND += ' && sudo usermod -aG testbed ${USER}' + \
                       ' && sudo usermod -aG docker ${USER}' + \
                       ' && sudo usermod -aG lxd ${USER}' + \
                       ' || echo "No group lxd"' + \
                       ' && sudo touch /home/${USER}/.Xauthority ' + \
                       ' && sudo chown -R ${USER}:${USER} /home/${USER}/.'

            # When allocating a container, modify bash_profile in user's
            # base_home to contain the chosen image, and bind an ethernet
            # interface inside the container
            COMMAND += ' && sudo cp -r' + \
                       ' /home/${BASE_USER}/base_home/. /home/${USER}' + \
                       ' && sudo sed -i "s/run.sh/run.sh ${IMG_TYPE}/g"' + \
                       ' /home/${USER}/.bash_profile '
        else:
            COMMAND += ' && sudo usermod -aG sudo ${USER}' + \
                       ' && sudo usermod -aG usrp ${USER}' + \
                       ' || echo "No group usrp"' + \
                       '  && sudo usermod -aG lxd ${USER}' + \
                       ' || echo "No group lxd"' + \
                       ' && sudo cp -r /home/cbtm/* /home/${USER}/ ' + \
                       ' || echo "Nothing on home"' + \
                       '&& sudo chown -R ${USER}:${USER} /home/${USER}/.'

        if img_type == 'telosb':
            COMMAND += ' && sudo usermod -aG dialout ${USER}' + \
                       ' && sudo chown -R ${USER}:${USER} /opt/tinyos-2.1.2'

        COMMAND = COMMAND.replace('${USER}', user) \
                         .replace('${SSH_KEY}', ssh_key) \
                         .replace('${IMG_TYPE}', img_type) \
                         .replace('${BASE_USER}', base_user)

        self.log.debug('COMMAND: \n' + COMMAND)
        # Sometimes the connection is refused, probably because the ssh server
        # has not started yet.
        # This loops tries to create the user up to maximum_attempts times,
        # with a sleep_time interval (in seconds) between tries.
        attempts = 0
        maximum_attempts = 92
        sleep_time = 5
        std_error_msg = ('Warning: Permanently added %s (ECDSA) to ' % ip) + \
                        ('the list of known hosts.\nConnection to %s closed.'
                         % ip)

        while attempts < maximum_attempts:
            self.log.debug('Back at loop, attempts:   \n' + str(attempts))
            with outlock:
                args = ['-o', 'UserKnownHostsFile=/dev/null',
                        '-o', 'StrictHostKeyChecking=no']
                stdout, stderr = \
                    ctrl_utils.run_command(self.log, HOST, COMMAND, args=args)
            with outlock:
                self.log.debug('Stdout :' + str(stdout))
                self.log.debug('Stderr :' + str(stderr))

            # If the SSH connection was rejected, try again
            if stderr == std_error_msg or 'refused' in stderr:
                with outlock:
                    self.log.error('[CREATE USER] Connection Refused \
                        when creating user.' + ' Attempt :' + str(attempts))
                    self.log.debug('Stderr:\n' + str(stderr))
                    self.log.debug('Stdout:\n' + str(stdout))
                attempts += 1
                time.sleep(sleep_time)
            else:
                with outlock:
                    self.log.debug('[CREATE USER] Successfully created user.')
                    self.log.debug('Stderr:\n' + str(stderr))
                    self.log.debug('Stdout:\n' + str(stdout))
                break

    def delete_user(self):
        self.log.debug("=============ENTERING DELETE USER==============")
        user_name = ''

        ip = str(self.node.host.get_ip())

        base_user = str(self.node.host.get_user())

        fullpath = base_user + '@' + ip

        COMMAND = 'cat /etc/group | grep testbed'

        result, err = ctrl_utils.run_command(self.log, fullpath, COMMAND)

        if result:
            user_name = result.rstrip('\n').split(':')[-1]
        else:
            return False

        if user_name:
            COMMAND = 'sudo pkill -u ' + user_name

            result, err = ctrl_utils.run_command(self.log, fullpath, COMMAND)
            if 'error' in result:
                return False
            COMMAND = "docker rm -f $(docker ps -a | tail -n +2" + \
                      " | awk '{print $1}' ) &> /dev/null"

            result, err = ctrl_utils.run_command(self.log, fullpath, COMMAND)
            if 'error' in result:
                return False

            COMMAND = 'sudo deluser --remove-home ' + user_name

            result, err = ctrl_utils.run_command(self.log, fullpath, COMMAND)
            if 'error' in result:
                return False

            if 'Done.' in result:
                return True
        else:
            return False

    def isRawBeingUsed(self):
        host = self.node.get_host()
        fullpath = host.get_user() + "@" + host.get_ip()
        # check if there is any user in group testbed
        COMMAND = 'cat /etc/group | grep testbed'

        read, err = ctrl_utils.run_command(self.log, fullpath, COMMAND)

        result = str(read)[:-1].split(':')[-1]
        print 'RESULT SSH RAW IS BEING USED:', bool(result)

        # if there is a user in group testbed resource is already assigned
        return bool(result)

    def allocate(self, user, ssh_key, img_type, break_flag):
        self.create_user(user, ssh_key, self.node.host.get_ip(),
                         img_type, self.node.is_raw(),
                         self.node.host.get_user())

    def deallocate(self):
        self.delete_user()

    def get_status(self):
        return None, None, None

    def get_resource_info(self):
        return self.get_status()

    def start(self):
        pass

    def shutdown(self):
        pass

    def restart(self):
        pass


class VirtualMachine(CBTM_Resource):
    def __init__(self, log, node):
        super(VirtualMachine, self).__init__(log, node)

    def get_vm(self):
        '''
        Get VM name from an USRP Id, if the USRP is attached to a VM.

        Args:
            node (NodeCBTM): Resource
        Returns:
            vm_name (string): if such VM exists, -1 if the VM is not found
        '''
        host = self.node.get_host()
        conn = host.get_conn_info()

        vm_names = conn.get_all_vms()
        result = -1

        expected_name = self.get_vm_name()
        if vm_names != []:
            for vm in vm_names:
                if vm == expected_name:
                    result = vm
        else:
            result = -1
        return result

    def get_vm_name(self):
        """ Returns a string containing the default name for a VM
        defined in the current node
        """
        return 'basic_eu_' + str(self.node.get_id())

    def make_vm(self, user, ssh_key, img_type, break_flag):
        '''
        Create a new VM to be used with a USRP.

        Args:
            node (NodeCBTM): Node to be used
            img_type (string): Type of image to be used
            user (string): User for the VM
            ssh_key (string): SSH key for the user
        '''
        try:
            host = self.node.get_host()
            res_num = str(self.node.get_id())

            self.log.debug('Creating VM image. (This may take a while).')
            self.log.debug('Resource ' + str(res_num))

            if img_type not in self.node.get_images():
                self.log.warning('Unrecognized image type:' + str(img_type) +
                                 ' Getting plain image instead')
                img_type = self.node.get_default_image()

            ctrl_utils.copy_image('master-' + img_type, 'basic_eu_' +
                                  res_num, host)

            img_name = self.get_vm_name() + '.img'

            vm_xml = ctrl_utils.create_xml(self.node,
                                           ctrl_utils.get_pool_path(host) +
                                           img_name,
                                           img_type)
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
                out_ip = host.get_conn_info().get_vm_info(self.get_vm_name())
                if time.time() - time0 > 240:
                    out_ip = '0.0.0.0'
                    break
                time.sleep(check_interval)
            if out_ip != '0.0.0.0':
                self.create_user(user, ssh_key, out_ip, img_type,
                                 self.node.is_raw(), 'cbtm')
            return out_ip

        except RuntimeError as e:
            self.log.debug(str(e))
            return

    def destroy_vm(self):
        """
            Delete a VM

            Args:
                node (NodeCBTM): RESOURCE to be used
        """
        if self.node.is_raw():
            return

        host = self.node.get_host()
        # res_num = node.get_id()

        vm_name = self.get_vm()
        if vm_name != -1:
            self.log.debug("Deleting: " + str(vm_name))
            ctrl_utils.destroy_vm(host, vm_name)
        vol_name = self.get_vol()
        if vol_name != -1:
            vol_name = vol_name.split('.')[0]
            self.log.debug("Deleting: " + str(vol_name))
            ctrl_utils.del_image(vol_name, host)

    def start(self):
        """
        Args:
            node (NodeCBTM): RESOURCE to be used
        """
        if self.node.is_raw():
            return

        host = self.node.get_host()
        res_num = self.node.get_id()
        vm_name = self.get_vm()

        if vm_name == -1:
            self.log.debug('No VM found for Resource %s' % res_num)
        else:
            self.log.debug('Starting VM %s' % vm_name)
            ctrl_utils.start_vm(host, vm_name)

    def shutdown(self):
        """
           Args:
                node (NodeCBTM): RESOURCE to be used
        """
        if self.node.is_raw():
            return

        host = self.node.get_host()
        res_num = self.node.get_id()
        vm_name = self.get_vm()

        if vm_name == -1:
            self.log.debug('No VM found for USRP %s' % res_num)
        else:
            self.log.debug('Shutting Down VM %s' % vm_name)
            ctrl_utils.shutdown_vm(host, vm_name)

    def restart(self):
        """
        Args:
            node (NodeCBTM): RESOURCE to be used
        """
        if self.node.is_raw():
            return

        host = self.node.get_host()
        res_num = self.node.get_id()
        vm_name = self.get_vm()

        if vm_name == -1:
            self.log.debug('No VM found for USRP %s' % res_num)
        else:
            self.log.debug('Restarting VM %s' % vm_name)
            ctrl_utils.restart_vm(host, vm_name)

    def get_vol(self):
        '''
        Get Volume name from an USRP Id, if the volume exists.

        Args:
            conn_list (ConnInfo): Dictionary of Libvirt connections to the
            Racks usrp_num (int): USRP Id
        Returns:
            vol_name (string): Volume name if volume exists, -1 if it doesn't.
        '''

        host = self.node.get_host()
        conn = host.get_conn_info()

        img_name = self.get_vm_name() + '.img'

        vol_names = conn.get_all_vols()
        if img_name in vol_names:
            return img_name
        else:
            return -1

    def allocate(self, user, ssh_key, img_type, break_flag):
        self.make_vm(user, ssh_key, img_type, break_flag)

    def deallocate(self):
        self.destroy_vm()

    def get_status(self):
        host = self.node.get_host()
        try:
            conn_info = host.get_conn_info()
        except Exception:
            host_name = host.get_name()
            print('Could not find connection for the intended rack:',
                  host_name)
            raise

        try:
            dom = \
                conn_info.conn.lookupByName(self.get_vm_name())
            use = True
        except Exception as e:
            self.log.debug('ERROR checking VM status: ' + str(e))
            self.log.debug('This error is expected, since the existance \
                            of the vm is being checked')
            # self.log.warning("Cloud not find the USRP" + str(usrp_num))
            use = False
            booted = False
            ip = '0.0.0.0'

        if use:
            booted = dom.isActive()
            if booted:
                ip = conn_info.get_vm_info(self.get_vm_name())
            else:
                ip = '0.0.0.0'

        return use, booted, ip

    def get_resource_info(self):
        return self.get_status()


class OpenSTF(VirtualMachine):
    def __init__(self, log, node):
        super(OpenSTF, self).__init__(log, node)

    def get_command_compose_build(self):
        return 'cd /home/${USER}/openstf/ && \
                sudo docker-compose up -d --build &&\
                sudo usermod -aG docker ${USER}'

    def make_docker_compose(self, user, ssh_key, img_type, ip, base_user):

        try:
            self.log.debug('Try to build DOCKER-COMPOSE')

            HOST = base_user + '@' + ip

            COMMAND = str(self.get_command_compose_build())\
                .replace('${USER}', user)

            self.log.debug('COMMAND: \n' + COMMAND)
            args = ['-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'StrictHostKeyChecking=no']
            stdout, stderr = \
                ctrl_utils.run_command(self.log, HOST, COMMAND, args=args)

        except Exception as e:
            self.log.debug('Error build DOCKER-COMPOSE' + str(e))

    def allocate(self, user, ssh_key, img_type, break_flag):
        vm_ip = self.make_vm(user, ssh_key, img_type, break_flag)
        self.make_docker_compose(user, ssh_key, img_type, vm_ip, 'cbtm')


class OpenFlowSwitch(CBTM_Resource):
    def __init__(self, log, node):
        super(OpenFlowSwitch, self).__init__(log, node)


class RaspberryPI(CBTM_Resource):
    def __init__(self, log, node):
        super(RaspberryPI, self).__init__(log, node)

    def get_status(self):
        host = self.node.get_host()
        if self.isRawBeingUsed():
            use = True
            booted = True
            ip = host.get_ip()
        else:
            use = False
            booted = False
            ip = '0.0.0.0'
        return use, booted, ip

    def deallocate(self):
        super(RaspberryPI, self).deallocate()
        self.log.debug('Resource %s removed' %
                       self.node.host.get_name())


class TelosB(CBTM_Resource):
    def __init__(self, log, node):
        super(TelosB, self).__init__(log, node)


class Container(CBTM_Resource):
    def __init__(self, log, node):
        super(Container, self).__init__(log, node)

    def get_status(self):
        host = self.node.get_host()
        if self.isRawBeingUsed():
            use = True
            booted = True
            ip = host.get_ip()
        else:
            use = False
            booted = False
            ip = '0.0.0.0'
        return use, booted, ip

    def deallocate(self):
        super(Container, self).deallocate()
        self.log.debug('Resource %s removed' %
                       self.node.host.get_name())

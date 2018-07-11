import time
import logging
import threading
import subprocess

import ctrl_utils
from node import Node
from nodecbtm import NodeCBTM

outlock = threading.Lock()

class Resource(object):
    def __init__(self, log, res_num, basic_id):
	images = []
        self.log = log
	self.nodes = [Node((basic_id+count+1), 0, 0, [], 0, 0) for count in xrange(res_num)]

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
        self.log.debug('Creating user for usage in the VM')
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
                       ' && sudo cp -r' + \
                       ' /home/futebol/base_home/. /home/${USER}' + \
                       ' || echo "Nothing on base_home"' + \
                       ' && sudo chown -R ${USER}:${USER} /home/${USER}/.'

            if('ubuntu' in img_type) or ((img_type == 'ethanol') or
                                         (img_type == 'srslte')):

                # When allocating a container, modify bash_profile in user's
                # base_home to contain the chosen image, and bind an ethernet
                # interface inside the container
                COMMAND += '&& sudo sed -i "s/run.sh/run.sh ${IMG_TYPE}/g"' + \
                           ' /home/${USER}/.bash_profile '
        else:
            COMMAND += ' && sudo usermod -aG sudo ${USER}' + \
                       ' && sudo usermod -aG usrp ${USER}' + \
                       ' || echo "No group usrp"' + \
                       ' && sudo cp -r /home/cbtm/* /home/${USER}/ ' + \
                       ' || echo "Nothing on home"' + \
                       '&& sudo chown -R ${USER}:${USER} /home/${USER}/.'

        if img_type == 'telosb':
            COMMAND += ' && sudo usermod -aG dialout ${USER}' + \
                       ' && sudo chown -R ${USER}:${USER} /opt/tinyos-2.1.2'

        COMMAND = COMMAND.replace('${USER}', user) \
                         .replace('${SSH_KEY}', ssh_key) \
                         .replace('${IMG_TYPE}', img_type)

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
            # print 'before first lock'
            with outlock:
                # print 'inside first lock'
                ssh = subprocess.Popen(['ssh', '-o',
                                        'UserKnownHostsFile=/dev/null', '-o',
                                        'StrictHostKeyChecking=no', '-t', '%s'
                                        % HOST, COMMAND], shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
                # result = self.run_command(HOST, COMMAND)
                # print 'exiting first lock'
            # print 'before second lock'
            with outlock:
                # print 'inside second lock'
                stderr = ""
                stdout = ""
                stdout = ssh.stdout.read()
                stderr = ssh.stderr.read()
                self.log.debug('Stdout :' + str(stdout))
                self.log.debug('Stderr :' + str(stderr))
                # self.log.debug('[CREATE_USER] Stdout:' +
                #    str(result))
                # print 'exiting second lock'

            # If the SSH connection was rejected, try again
            if stderr == std_error_msg or 'refused' in stderr:
                # print 'before third lock'
                with outlock:
                    # print 'inside third lock'
                    self.log.error('[CREATE USER] Connection Refused \
                        when creating user.' + ' Attempt :' + str(attempts))
                    self.log.debug('Stderr:\n' + str(stderr))
                    self.log.debug('Stdout:\n' + str(stdout))
                    # self.log.debug('Stdout:\n' + str(result))
                    # print 'exiting third lock'
                attempts += 1
                time.sleep(sleep_time)
            else:
                # print 'before fourth lock'
                with outlock:
                    # print 'inside fourth lock'
                    self.log.debug('[CREATE USER] Successfully created user.')
                    self.log.debug('Stderr:\n' + str(stderr))
                    self.log.debug('Stdout:\n' + str(stdout))
                    # print 'exiting fourth lock'
                break
      

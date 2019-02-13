#!/usr/bin/env python

import logging
import threading
from resource_operator import ResourceOperator


class CommandHandler(object):

    def __init__(self, args, port):

        self.port = port
        self.operator = ResourceOperator(args, port)
        self.operator.log = logging.getLogger("cbtm_logger")
        self.operator.log.debug("Initializing Handler")

        self.make_threads = {}
        self.make_vlan_threads = {}
        self.break_flags = {}
        self.del_threads = {}

        self.accepted_commands = ['request_unit', 'grid_status',
                                  'release_unit', 'unit_status',
                                  'shutdown_unit', 'start_unit',
                                  'restart_unit', 'make_clean']

    def handle(self, command, args):
        self.update()
        self.operator.log.debug("Received command: " + str(command) +
                                ' with: ' + str(args) + '.')
        msg = 'Bad command: "%s"' % command
        if command in self.accepted_commands:
            if len(args) > 0:
                try:
                    msg = getattr(self, command)(*args)
                except Exception as e:
                    self.operator.log.debug('ERRO EM handle: ')
                    self.operator.log.debug(str(e))

        return msg

    def request_unit(self, args):
        self.operator.log.debug("Unit Requested: " + str(args))
        try:
            res_num, img_type, user, ssh_key = args.split(',')
        except Exception:
            msg = "[REQUEST_UNIT] ERROR: invalid argument number"
            self.operator.log.debug(msg)
            deny = True
        else:
            # Looks up the corresponding host name to the specified RESOURCE
            # number
            node = self.operator.rm.get_resource(res_num)
            # host = node.get_host()
            if node is None:
                m = "[REQUEST_UNIT] Resource unknown or unavailable.Try Again."
                self.operator.log.debug(m)
                deny = True
            else:
                use, booted, ip = self.operator.check_resource_status(node)
                if use:
                    deny = True
                else:
                    deny = False
        # ============ ACCEPT OR DENY REQUEST DEPENDING ON RESOURCE
        # AVAILABILITY
        if deny:
            msg = 'Denied'
        else:
            msg = 'Accepted'
            f = threading.Event()
            t = threading.Thread(target=self.operator.allocate_resource,
                                 args=(node, img_type, user, ssh_key, f))

            t.name = 'allocate_resource ' + str(res_num) + '_' + \
                str(t.name.lower())

            t.start()

            self.make_threads[res_num] = t
            self.break_flags[res_num] = f

        return 'request_status:' + msg

    def grid_status(self, args):
        self.operator.log.debug("Grid Status: " + str(args))

        resources = self.operator.check_grid_resources(self.operator.rm
                                                       .get_resources())
        engaged = []
        for key in resources.use.keys():
            if resources.use[key]:
                engaged.append(key)
        engaged.sort()
        engaged = [str(k) for k in engaged]
        return 'grid_status:\n\tIn use:' + ','.join(engaged)

    def release_unit(self, res_num):
        """
            Deletes the VM
        """
        node = self.operator.rm.get_resource(res_num)
        use, boot, vm_ip = self.operator.check_resource_status(node)
        """
            Try:
                self.break_flags[usrp_num].set()
            except KeyError:
                #This usrp has not been requested yet (in this session)
                pass
        """
        if use:
            t = threading.Thread(target=self.operator.deallocate_resource,
                                 args=(node,))
            t.name = 'destroy_usrp_' + str(res_num) + str(t.name.lower())
            t.start()
            self.del_threads[res_num] = t
            return 'ok'
        else:
            return 'not_in_use'

    def unit_status(self, res_num):
        """
            Get the satus of a particular USRP. Possible status are:
            free: No VM is defined for that particular USRP
            vm IP: If the machine is booted and ready, the IP is replied.
            wait: The VM is being created. Wait for completion.

            Returns:
                msg (string): String that indicates the status of the USRP.
        """
        # print('In unit_status ' + str(res_num)+ '.')
        try:
            # Check if the VM is being made
            assert(self.make_threads[res_num].is_alive())
        except (AssertionError, KeyError):
            # The VM is not being made, get its info.
            try:
                node = self.operator.rm.get_resource(res_num)
                # print str(node)
                use, boot, vm_ip = self.operator.check_resource_status(node)
                if not use:
                    self.operator.log('resource  ' + str(res_num) + ' returned free status!!!')
                    return 'unit_status:free'
                elif boot:
                    if str(vm_ip) == '0.0.0.0':
                        self.operator.log.debug('resource  ' +
                                                str(res_num) +
                                                ' RETURNED IP 0.0.0.0 ' +
                                                'as normal IP')
                        return 'unit_status:failed'
                    return 'unit_status:' + str(vm_ip)
                else:
                    return 'unit_status:failed'
            except Exception as e:
                print 'ERROR: ' + str(e)
                return 'unit_status:failed'
        else:
            # The VM is being made, wait.
            return 'unit_status:wait'

    def shutdown(self):
        for key in self.break_flags.keys():
            self.break_flags[key].set()

    def start_unit(self, res_num):
        self.operator.start_resource(self.operator.rm.get_resource(res_num))
        # self.operator.start_vm(self.operator.rm.get_resource(res_num))
        return 'ok'

    def shutdown_unit(self, res_num):
        self.operator.stop_resource(self.operator.rm.get_resource(res_num))
        return 'ok'

    def restart_unit(self, res_num):
        self.operator.restart_resource(self.operator.rm.get_resource(res_num))
        return 'ok'

    def make_clean(self, non_active_resources):
        non_active_resources = non_active_resources.split(',')
        non_active_resources = [node
                                for node in self.operator.rm.get_resources()
                                .itervalues()
                                if str(node.get_id()) in non_active_resources]
        self.operator.make_clean(non_active_resources)
        return 'ok'

    def update(self):
        self.operator.rm.update()

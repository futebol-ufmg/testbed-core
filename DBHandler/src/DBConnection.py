#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MySQLdb


class Singleton(type):
    """
    Implementation of the Singleton design pattern in order
    to allow a unique instance of a class
    """

    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class DBConnection(object):
    __metaclass__ = Singleton

    def __init__(self, host='127.0.0.1', username='root',
                 password='', db_name='testbd'):
        self.db = MySQLdb.connect(host=host,         # IP of DB host
                                  user=username,     # Username for the DB
                                  passwd=password,   # DB password
                                  db=db_name,)       # DB name
        self.cursor = self.db.cursor()

    def __del__(self):
        self.cursor.close()
        self.db.close()

    def list_equipments(self):
        query = ("SELECT * from Equipment")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.fetchall(), 'success'

    def get_available_equipments(self):
        query = ("SELECT * from Equipment WHERE available = TRUE")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.fetchall(), 'success'

    def get_available_resources(self):
        query = ("SELECT r.resourceID from Resource r NATURAL JOIN Equipment e\
                 WHERE e.available = 1")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        # Convert each result from tuple (resource ID,) to integer and return
        return map(lambda x: int(x[0]), self.cursor.fetchall()), 'success'

    def get_all_resources(self):
        query = \
            ("SELECT r.resourceID from Resource r NATURAL JOIN Equipment e \
              order by r.resourceID")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        # Convert each result from tuple (resource ID,) to integer and return
        return list(map(lambda x: int(x[0]), self.cursor.fetchall())), \
            'success'

    def get_available_slivers(self):
        query = ("SELECT DISTINCT s.name, s.type FROM (Resource r\
        NATURAL JOIN Equipment e) JOIN Sliver s ON r.sliverID = s.sliverID\
        WHERE e.available=1")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.fetchall(), 'success'

    def get_active_vlans(self):
        """
        Return all the VLANs ranges (IP and Netmask) currently in use
        """
        query = ("SELECT v.ip, v.netmask FROM Vlan v")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.fetchall(), 'success'

    def get_resource_equipment_id(self, resource_id):
        """
        Return the equipment ID associated to a specified resource
        """
        query = ("SELECT r.equipmentID FROM Resource r WHERE \
                  r.resourceID = " + str(resource_id) + "")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(lambda x: int(x[0]), self.cursor.fetchall()), 'success'

    def get_resource_allocation_id(self, resource_id):
        """
        Return the allocation ID associated to the resource specified
        """
        query = ("SELECT ra.allocationID FROM ResourceHasAllocation ra WHERE \
                 ra.resourceID = " + str(resource_id) + "")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(lambda x: int(x[0]), self.cursor.fetchall()), 'success'

    def get_equipment_switch_info(self, equipment_id):
        """
        Return the equipment's configuration on the switch
        """
        query = ("SELECT sp.numPort, sp.ip, sp.switchDPID, sp.mac, s.type FROM \
                (SwitchPorts sp NATURAL JOIN Switch s) \
                WHERE sp.equipmentID = " + str(equipment_id) + "")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.fetchall(), 'success'

    def get_experiment_allocations(self, experiment_id):
        """
        Return a list of allocations for an experiment according to its ID
        """
        query = ("SELECT a.allocationID FROM Allocation a \
                 WHERE a.experimentID = %d" % (int(experiment_id)))
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(lambda x: int(x[0]), self.cursor.fetchall()), 'success'

    def is_resource_available(self, resource_id):
        """
        Check whether a specified resource is available and return True or
        False
        """
        result_query_resources = self.get_available_resources()

        # Error on selecting resources from database
        if result_query_resources[0] == -1:
            return result_query_resources

        # Search for the resource ID in the map returned previously
        if resource_id in result_query_resources[0]:
            return True
        return False

    def create_experiment(self, start_time, end_time, username):
        """
        Create a new experiment and return its PK generated
        """
        query = ("INSERT INTO Experiment (startDate, endDate, username) \
                 VALUES('%s', '%s', '%s')" %
                 (str(start_time), str(end_time), str(username)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

    def update_experiment_time(self, experiment_id, new_start_time,
                               new_end_time):
        """
        Update the experiment duration by resetting the start and end times
        """
        query = ("UPDATE Experiment e SET startDate = " +
                 str(new_start_time) +
                 " endDate = " + str(new_end_time) +
                 " WHERE e.experimentID = " +
                 str(experiment_id))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def __free_experiment_equipments(self, experiment_id):
        """
        Set the status of the experiment's used equipments to available
        """
        query = ("UPDATE Equipment e NATURAL JOIN Resource r NATURAL JOIN \
                 ResourceHasAllocation rha NATURAL JOIN Allocation a \
                 SET e.available = 1 WHERE a.experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def delete_experiment(self, experiment_id):
        """
        Delete an experiment by its ID and free the used equipments
        """
        free_equip_result = self.__free_experiment_equipments(experiment_id)
        if free_equip_result[0] == -1:  # Query error
            return free_equip_result    # Return error message

        query = ("DELETE FROM Experiment WHERE experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def delete_user_experiments(self, username):
        """
        Delete all experiments of a user by its username
        """
        query = ("DELETE FROM Experiment WHERE username = '%s'" %
                 str(username))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def __create_experiment_allocation(self, experiment_id):
        """
        Create an allocation for an experiment and return the PK generated
        The result is used to allocate a resource since it is an N:N relation
        """
        query = ("INSERT INTO Allocation (experimentID) \
                 VALUES('%d')" % (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

    def __create_resource_allocation(self, resource_id, allocation_id):
        """
        Create a resource allocation by relating the Allocation and Resource
        tables
        """
        query = ("INSERT INTO ResourceHasAllocation (resourceID, allocationID) \
                VALUES(%d, %d)" % (int(resource_id), int(allocation_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def __set_equipment_availability(self, resource_id, status):
        """
        Set equipment available status as False, indicating that it is
        being used
        """
        query = ("UPDATE Equipment e NATURAL JOIN Resource r \
                 SET e.available = %d \
                 WHERE r.resourceID = %d" % (int(status), int(resource_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 'success'

    def create_allocation(self, experiment_id, resource_id):
        """
        Visible method to allocate a resource for an experiment
        """

        # Firstly, insert the experiment into the Allocation table
        exp_alloc_result = self.__create_experiment_allocation(experiment_id)

        if exp_alloc_result[0] == -1:    # Error on experiment allocation query
            return exp_alloc_result      # Return the error message

        # Secondly, relate the previous allocation with the resource specified
        allocation_id = exp_alloc_result[0]
        resource_alloc_result = \
            self.__create_resource_allocation(resource_id, allocation_id)

        if resource_alloc_result == 'success':
            # Make the correspondent equipment unavailable
            new_equip_status = 0
            equip_update_result = \
                self.__set_equipment_availability(resource_id,
                                                  new_equip_status)

            if equip_update_result[0] == -1:
                # Error on equipment status update query
                return equip_update_result    # Return the error message
            return allocation_id, 'success'

        # Return error message in case of resource allocation query failure
        return resource_alloc_result

    def create_vlan(self, allocation_id, ip, netmask, controller):
        """
        Create a new VLAN and return the PK generated
        """
        query = ("INSERT INTO Vlan (ip, netmask, controller, allocationID) \
                 VALUES('%s', '%s', '%s', '%d')" %
                 (str(ip), str(netmask), str(controller), int(allocation_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid(), 'success'

    def create_wlan(self, vlan_id, ssid, psk, auth, channel, tx_power):
        """
        Create a new WLAN for a VLAN and return its PK, which is also the
        VLAN's PK
        """
        query = ("INSERT INTO Wlan (vlanID, ssid, psk, auth, channel, txPower) \
                 VALUES('%d', '%s', '%s', '%s', '%d', '%d')" %
                 (int(vlan_id), str(ssid), str(psk), str(auth),
                  int(channel), int(tx_power)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid(), 'success'

    def add_switch_ports(self, numPort, ip, switchDPID, equipmentCod, mac):
        query = "INSERT INTO SwitchPorts \
                 (numPort, ip, switchDPID, equipmentID, mac) VALUES \
                 ('%s', '%s', '%s', '%s', '%s')" % (str(numPort), str(ip),
                                                    str(switchDPID),
                                                    str(equipmentCod),
                                                    str(mac))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return 0, 'success'

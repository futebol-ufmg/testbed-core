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

    def get_image_id_from_name(self, image_name):
        query = ("SELECT imageID FROM Image \
                 WHERE name = '%s'" % (str(image_name)))
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        # return self.cursor.fetchall()[0], 'success'
        return self.cursor.lastrowid, 'success'

    def get_sliver_id_from_resource_image(self, resource_id, image_id):

        query = ("SELECT s.sliverID FROM (Resource r JOIN Sliver s \
                 ON s.sliverID = r.sliverID) JOIN Image i ON \
                 (i.sliverID = s.sliverID AND i.sliverID = r.sliverID) \
                 WHERE r.resourceID = (%d) and i.imageID = (%d)" %
                 (int(resource_id), int(image_id)))
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

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

    def update_experiment_time(self, experiment_id, new_start_time, new_end_time):
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
        return self.cursor.lastrowid, 'success'

    def get_expired_experiments(self, now):
        query = ("SELECT experimentID from Experiment " +
                 " WHERE startDate < '" + str(now) + "' AND" +
                 " '" + str(now) + "' > endDate ")
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return [elem[0] for elem in self.cursor.fetchall()], 'success'

    def get_experiment_nodes_resource_id(self, experiment_id):
        """
        Retrieve experiment Nodes from DB
        """
        query = ("SELECT n.resourceID FROM Experiment e NATURAL JOIN Node n \
                  WHERE e.experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return [elem[0] for elem in self.cursor.fetchall()], 'success'

    def get_experiment_vlans(self, experiment_id):
        """
        Retrieve experiment Vlans from DB
        """
        query = ("SELECT v.vlanID FROM Experiment e NATURAL JOIN Vlan v \
                  WHERE e.experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return [elem[0] for elem in self.cursor.fetchall()], 'success'

    def __free_experiment_nodes(self, experiment_id):
        """
        Delete Node rows to free all allocations of the experiment
        """
        # Set experiment equipments as available
        query = ("UPDATE Equipment eq \
                  NATURAL JOIN Resource r \
                  NATURAL JOIN Node n \
                  NATURAL JOIN Experiment exp \
                  SET eq.available = 1 \
                  WHERE exp.experimentID = %d" % int(experiment_id))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e

        query = ("DELETE FROM Node WHERE experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

    def __free_experiment_vlans(self, experiment_id):
        """
        Delete Vlan rows to free all allocations of the experiment
        """
        query = ("DELETE FROM Vlan WHERE experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

    def __free_experiment_vlan_nodes(self, experiment_id):
        """
        Delete Vlan_Node rows to free all allocations of the experiment
        """
        query = ("SELECT vl.nodeID FROM Vlan_Node vl \
                  NATURAL JOIN Node n \
                  WHERE n.experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        ids = [int(elem[0]) for elem in self.cursor.fetchall()]

        for nodeID in ids:
            query = ("DELETE FROM Vlan_Node \
                     WHERE nodeID = %d" %
                     (int(nodeID)))
            try:
                self.cursor.execute(query)
                self.db.commit()
            except Exception as e:
                return -1, e

        return self.cursor.lastrowid, 'success'

    def delete_experiment(self, experiment_id):
        """
        Delete an experiment by its ID and free the used equipments
        """
        free_vlan_node_result, success = \
            self.__free_experiment_vlan_nodes(experiment_id)
        if 'success' not in success:  # Query error
            return success            # Return error message

        free_equip_result, success = \
            self.__free_experiment_nodes(experiment_id)
        if 'success' not in success:  # Query error
            return success            # Return error message

        free_vlan_result, success = \
            self.__free_experiment_vlans(experiment_id)
        if 'success' not in success:  # Query error
            return success            # Return error message

        query = ("DELETE FROM Experiment WHERE experimentID = %d" %
                 (int(experiment_id)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

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

    def __create_node_allocation(self, experiment_id, resource_id, image_id, ip, netmask):
        """
        Create an allocation for an experiment and return the PK generated
        The result is used to allocate a resource since it is an N:N relation
        """
        sliver_id = self.get_sliver_id_from_resource_image(resource_id,
                                                           image_id)
        if sliver_id[0] == -1:    # The Sliver don't exists
            return sliver_id

        query = ("INSERT INTO Node (resourceID, imageID, \
                sliverID, experimentID, provisioned, ip, netmask) \
                VALUES((%d), (%d), (%d), (%d),(%d))"
                 % (int(resource_id),
                    int(sliver_id),
                    int(image_id),
                    int(experiment_id),
                    str(ip),
                    str(netmask)))
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

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
        return 0, 'success'


    def create_vlan_node(self, vlan_id, node_id):
        """
        Create a new Vlan_Node entry from Vlan_id and Node_id
        """
        query = ("INSERT INTO Vlan_Node \
                 (vlanID, nodeID) \
                 VALUES(" + str(vlan_id) + ", " + str(node_id) + ")")
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

    def create_allocation(self, experiment_id, resource_id, image_name, ip, netmask):
        """
        Visible method to allocate a resource for an experiment
        """

        # Firstly, insert the experiment into the Node table
        # resource_alloc_result = self.__create_experiment_allocation(experiment_id, resource_id, image_id)
        image_id, success = self.get_image_id_from_name(image_name)
        if 'success' not in success:
            return -1, 'error'

        node_alloc_result = \
            self.__create_node_allocation(experiment_id, resource_id,
                                          image_id,
                                          ip, netmask)

        if node_alloc_result[0] == -1:    # Error on experiment allocation query
            return node_alloc_result      # Return the error code
            # Make the correspondent equipment unavailable
            new_equip_status = 0
            equip_update_result = \
                self.__set_equipment_availability(resource_id,
                                                  new_equip_status)

            if equip_update_result[0] == -1:
                # Error on equipment status update query
                return equip_update_result    # Return the error message
            return node_alloc_result[0], 'success'

        # Return error message in case of resource allocation query failure
        return node_alloc_result

    def create_vlan(self, ip, netmask, controller, tenant_id, experiment_id):
        """
        Create a new VLAN and return the PK generated
        """
        query = ("INSERT INTO Vlan \
                 (ip, netmask, controller, tenant_id, experimentID, provisioned) \
                 VALUES('" + str(ip) + "', '" + str(netmask) + "', '" +
                 str(controller) + "', " + str(int(tenant_id)) + ", " +
                 str(int(experiment_id)) + ", " + str(0) + ")")
        try:
            self.cursor.execute(query)
            self.db.commit()
        except Exception as e:
            return -1, e
        return self.cursor.lastrowid, 'success'

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

    def get_all_slivers(self):
        """
        Return the list of names of all Slivers
        """
        query = ("SELECT * from Sliver")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(list, self.cursor.fetchall()), 'success'

    def get_sliver_images(self, sliver_name='', sliver_id=None):
        """
        Return a list of image names by relating the Sliver and Image
        tables with a specific sliver name
        """
        if sliver_id is not None:
            query = ("SELECT I.name from Image I INNER JOIN Sliver S \
                     ON I.sliverID = S.sliverID WHERE S.sliverID = " +
                     str(sliver_id))
        else:
            query = ("SELECT I.name from Image I INNER JOIN Sliver S \
                     ON I.sliverID = S.sliverID WHERE S.name = '" +
                     str(sliver_name) + "'")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(lambda x: x[0], self.cursor.fetchall()), 'success'

    def get_default_image(self, sliver_name='', sliver_id=None):
        """
        Return a list of default image names by relating the
        Sliver and Image tables with a specific sliver name
        """
        if sliver_id is not None:
            query = ("SELECT I.name from Image I INNER JOIN Sliver S \
                     ON I.sliverID = S.sliverID \
                     WHERE S.sliverID = " + str(sliver_id) +
                     " AND I.default=1")
        else:
            query = ("SELECT I.name from Image I INNER JOIN Sliver S \
                     ON I.sliverID = S.sliverID \
                     WHERE S.name = '" + str(sliver_name) +
                     "' AND I.default=1")
        try:
            self.cursor.execute(query)
            result = str(self.cursor.fetchall()[0][0])
        except Exception as e:
            return -1, e
        return result, 'success'

    def get_resource_usb(self, resource_number):
        """
        Return a list of resource usb related to a specific resource number
        """
        query = ("SELECT usb from Resource WHERE resourceID = " +
                 str(resource_number))
        try:
            self.cursor.execute(query)
            result = str(self.cursor.fetchall()[0][0])
        except Exception as e:
            return -1, e
        return result, 'success'

    def get_sliver_type(self, sliver_name):
        """
        Return a list of types from Sliver related to a specific sliver name
        """
        query = ("SELECT type from Sliver WHERE name = '" +
                 str(sliver_name) + "'")
        try:
            self.cursor.execute(query)
            result = str(self.cursor.fetchall()[0][0])
        except Exception as e:
            return -1, e
        return result, 'success'

    def get_resources_in_sliver(self, sliver_id=None, sliver_name=''):
        """
        Return a list of resource IDs by relating the Sliver and Resource
        tables with a specific sliver ID and then converts that
        list to integers
        """
        if sliver_id is not None:
            query = ("SELECT R.resourceID from Resource R INNER JOIN Sliver S \
                     ON R.sliverID = S.sliverID WHERE S.sliverID = " +
                     str(sliver_id))
        else:
            query = ("SELECT R.resourceID from Resource R INNER JOIN Sliver S \
                     ON R.sliverID = S.sliverID WHERE S.name = '" +
                     str(sliver_name) + "'")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(lambda x: int(x[0]), self.cursor.fetchall()), 'success'

    def get_equipment_info_control_network(self):
        """
        Return a list of lists, containing [name, ip, user]
        for each equipment connected to the control network (switch DPID ==
        00:00:00:00:00:00)
        """
        query = ("SELECT R.resourceID, SL.sliverID, E.name, SP.ip, E.user\
                  FROM SwitchPorts SP\
                  INNER JOIN Equipment E\
                  INNER JOIN Resource R INNER JOIN Sliver SL\
                  ON SP.equipmentID = E.equipmentID\
                  AND E.equipmentID=R.equipmentID\
                  AND R.sliverID = SL.sliverID\
                  WHERE SP.switchDPID = '00:00:00:00:00:00'")
        try:
            self.cursor.execute(query)
        except Exception as e:
            print(e)
            print(repr(e))
            return -1, e
        return map(list, self.cursor.fetchall()), 'success'

    def get_equipment_info_data_network(self):
        """
        Return a list of lists, containing [name, ip, user]
        for each equipment connected to the data network (switch DPID ==
        48:6e:73:02:05:ee)
        """
        query = ("SELECT R.resourceID, SL.name, SL.type, E.name, SP.ip, E.user\
                  FROM SwitchPorts SP\
                  INNER JOIN Equipment E\
                  INNER JOIN Resource R INNER JOIN Sliver SL\
                  ON SP.equipmentID = E.equipmentID\
                  AND E.equipmentID=R.equipmentID\
                  AND R.sliverID = SL.sliverID\
                  WHERE SP.switchDPID = '00:00:00:00:00:00'")
        try:
            self.cursor.execute(query)
        except Exception as e:
            return -1, e
        return map(list, self.cursor.fetchall()), 'success'

#!/usr/bin/env python
'''
    User Resources Module. Module will store the username and password
    for the Zabbix server and the MySQL Database.
    This module will be imported by multiple modules
    (Coordinator, AM, and CBTM), but initialized only once.
    Author: Pedro Alvarez
    Modified by: Matheus Nunes
'''


from getpass import getuser
# Get MySql User name and password
db_user = getuser()
db_passwd = "dbpasswd"
db_host = "127.0.0.1"
db_name = "USERS"

#!/bin/bash
# Script to change the IP of the interface connected to the USPR @ a Virtual machine.
# Copy this file to /etc and add the following lines to /etc/rc.local:
#   cd /etc
#   ./change_usrp_ip.sh
#   exit 0

IF=ens4
mac_addr=$(cat /sys/class/net/$IF/address)

if [ $mac_addr == 'b0:83:fe:da:91:2a' ]
    then
    ifconfig $IF 10.0.11.1/8
elif [ $mac_addr == 'c8:1f:66:dc:31:14' ]
    then
    ifconfig $IF 10.0.12.1/8
elif [ $mac_addr == 'c8:1f:66:dc:31:15' ]
    then
    ifconfig $IF 10.0.13.1/8
elif [ $mac_addr == 'c8:1f:66:dc:31:16' ]
    then
    ifconfig $IF 10.0.14.1/8
elif [ $mac_addr == 'f8:bc:12:34:f4:b9' ]
    then
    ifconfig $IF 10.0.21.1/8
elif [ $mac_addr == 'f8:bc:12:34:f4:ba' ]
    then
    ifconfig $IF 10.0.22.1/8
elif [ $mac_addr == 'f8:bc:12:34:f4:bb' ]
    then
    ifconfig $IF 10.0.23.1/8
elif [ $mac_addr == 'b0:83:fe:da:92:32' ]
    then
    ifconfig $IF 10.0.24.1/8
elif [ $mac_addr == 'c8:1f:66:ef:59:58' ]
    then
    ifconfig $IF 10.0.31.1/8
elif [ $mac_addr == 'c8:1f:66:ef:59:59' ]
    then
    ifconfig $IF 10.0.32.1/8
elif [ $mac_addr == 'c8:1f:66:ef:59:5a' ]
    then
    ifconfig $IF 10.0.33.1/8
elif [ $mac_addr == 'b0:83:fe:da:92:33' ]
    then
    ifconfig $IF 10.0.34.1/8
elif [ $mac_addr == 'c8:1f:66:da:b7:fd' ]
    then
    ifconfig $IF 10.0.41.1/8
elif [ $mac_addr == 'c8:1f:66:da:b7:fe' ]
    then
    ifconfig $IF 10.0.42.1/8
elif [ $mac_addr == 'c8:1f:66:da:b7:ff' ]
    then
    ifconfig $IF 10.0.43.1/8
elif [ $mac_addr == 'b0:83:fe:da:92:34' ]
    then
    ifconfig $IF 10.0.44.1/8
fi

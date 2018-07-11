#Test if libvirt is working

sudo libvirtd -d
virsh -c 'qemu:///system' list --all
virsh -c 'qemu:///system' domifaddr

#This should throw the error: error: command 'domifaddr' requires <domain> option.

#If the command is not recognized, the CBTM will not work properly.

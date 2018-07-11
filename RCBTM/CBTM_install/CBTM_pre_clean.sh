#remove any version of libvirt currently installed

ps -aux | grep libvirt | awk '{print $2}' | xargs sudo kill

sudo apt-get purge libvirt-dev libvirt-bin libvirt0

find / -name libvirt | xargs sudo rm -rf
find / -type f -name "*libvirt*" | xargs sudo rm -rf



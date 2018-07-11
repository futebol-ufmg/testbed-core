#libvirt installation script

sudo apt-get install gcc make pkg-config libxml2-dev libgnutls-dev libdevmapper-dev libcurl4-gnutls-dev python-dev libpciaccess-dev libxen-dev libnl-3-dev libnl-route-3-200 libnl-route-3-dev libyajl-dev uuid-dev qemu-kvm bridge-utils dnsmasq ebtables

cd ~/

wget libvirt.org/sources/libvirt-1.3.4.tar.gz
tar -xzf libvirt-1.3.4.tar.gz

cd libvirt-1.3.4
./autogen.sh --system
make
sudo make install
sudo ldconfig

sudo groupadd libvirtd
sudo adduser `id -un` libvirtd
sudo cp libvirtd.conf /etc/libvirt/libvirtd.conf
sudo cp qemu.conf /etc/libvirt/qemu.conf

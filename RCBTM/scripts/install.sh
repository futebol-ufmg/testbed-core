# Dependencies installation script

# Install apt dependencies
sudo apt-get install -qy gcc make pkg-config libxml2-dev libgnutls-dev \
libdevmapper-dev libcurl4-gnutls-dev python-dev python-pip libpciaccess-dev \
libxen-dev libnl-3-dev libnl-route-3-200 libnl-route-3-dev libyajl-dev \
uuid-dev qemu-kvm bridge-utils dnsmasq ebtables python-libvirt python3-libvirt 

# Install python dependencies
pip install --upgrade pip setuptools wheel Twisted isc_dhcp_leases

# Install libvirt
cd /tmp

wget libvirt.org/sources/libvirt-1.3.4.tar.gz
tar -xzf libvirt-1.3.4.tar.gz

cd libvirt-1.3.4
./autogen.sh --system
make
sudo make install
sudo ldconfig

# Add groups
sudo groupadd libvirtd
sudo adduser `id -un` libvirtd

sudo groupadd testbed
sudo usermod -aG sudo futebol

# Adjust configuration files
sudo sed -i "s/\/usr\/local\/lib\
/\/usr\/lib\\n\/usr\/local\/lib/g" /etc/ld.so.conf.d/libc.conf

sudo sed -i "s/#unix_sock_group\ =\ \"libvirt\"\
/unix_sock_group\ =\ \"libvirtd\"/g" /etc/libvirt/libvirtd.conf

sudo sed -i "s/#unix_sock_rw_perms\ =\ \"0770\"\
/unix_sock_rw_perms\ =\ \"0770\"/g" /etc/libvirt/libvirtd.conf

sudo sed -i "s/#auth_unix_ro\ =\ \"none\"\
/auth_unix_ro\ =\ \"none\"/g" /etc/libvirt/libvirtd.conf

sudo sed -i "s/#auth_unix_rw\ =\ \"none\"\
/auth_unix_rw\ =\ \"none\"/g" /etc/libvirt/libvirtd.conf

sudo sed -i "s/#stdio_handler\ =\ \"logd\"\
/stdio_handler\ =\ \"file\"/g" /etc/libvirt/qemu.conf

# Install UHD and USRP drivers
sudo apt-get install -qy gnuradio 
sudo apt-get install libuhd-dev libuhd003 uhd-host
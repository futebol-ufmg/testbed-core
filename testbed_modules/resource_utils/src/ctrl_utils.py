#!/usr/bin/env python

import subprocess

DIR_NAME = '../resources/'
POOL_NAME = 'cbtm-pool'
BASE_FILE = 'basic_eu.xml'
POOL_PATH = '/home/${USER}/cbtm-pool/'


def get_pool_path(host):
    return POOL_PATH.replace('${USER}', host.get_user())


def run_command(log, fullpath, COMMAND, args=[]):
    result = 'error'
    try:
        ssh = subprocess.Popen(["ssh"] + args +
                               ["%s" % fullpath, COMMAND],
                               shell=False, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

        result = ssh.stdout.read()
        err = ssh.stderr.read()
        if err:
            log.debug('ERROR on ctrl_utils run_command: ' + str(err))
    except Exception as e:
        log.debug("EXCEPTION on ctrl_utils run_command: " + str(e))
        return 'error'

    return str(result), err


def read_xml(xmlPath):
    '''
    Read the bare XML template
    '''
    try:
        template = open(xmlPath, 'r')
    except Exception:
        print('Error: Cannot open the file ' + xmlPath)
        exit(1)

    xml = template.read()
    template.close()

    return xml


def create_xml(node, image, img_type):
    '''
    Creates a XML template based on the Args assigned.

    Args:
        node (NodeCBTM): Resource
        iface (string): Interface that is connected to USRP
        image (string): Full path to VM image
        mac_addr (string): Macc Address of the interface connected to USRP

    Returns:
        full_template (string): A full template with the defined specifications
    '''

    bare_template = read_xml(DIR_NAME + BASE_FILE)

    startusb = ''
    endusb = ''
    vendor = ''
    product = ''
    if node.get_usb():
        vendor, product = node.get_usb().split(':')
        vendor = '0x' + vendor
        product = '0x' + product
    else:
        startusb = '<!--'
        endusb = '-->'

    full_template = bare_template \
        .replace('${DOM_NAME}', 'basic_eu_' + str(node.get_id())) \
        .replace('${AMOUNT_CPU}', str(8)) \
        .replace('${AMOUNT_MEMORY}', str(8)) \
        .replace('${IMG_PATH}', image) \
        .replace('${STARTUSB}', startusb)\
        .replace('${VENDOR}', vendor)\
        .replace('${PRODUCT}', product)\
        .replace('${ENDUSB}', endusb)

    return full_template


def define_and_boot_vm(host, template):
    '''
    Define (create) and boot a Virtual Machine.

    Args:
        conn_list (ConnInfo): Libvirt connections to the Racks
        host (HostCBTM): Host where the VM will be located
        template (string): XML template created using create_xml()
    '''
    try:
        conn = host.get_conn_info().conn
    except KeyError:
        host_name = host.get_name()
        print('Could not find connection for the intended rack:', host_name)
        raise

    try:
        dom = conn.defineXML(template)
    except Exception:
        print('Could not define VM')
        raise

    try:
        dom.create()
    except Exception:
        print('Could not boot VM')
        raise


def destroy_vm(host, domain_name):
    '''
    Undefine (destroy) a Virtual Machine.

    Args:
        host (HostCBTM): Host where the VM will be located
        domain_name (string): Name of the VM
    '''
    try:
        conn = host.get_conn_info().conn
    except KeyError:
        host_name = host.get_name()
        print('Could not find connection for the intended rack:', host_name)
        raise

    dom = conn.lookupByName(domain_name)
    if dom.isActive():
        dom.destroy()
    dom.undefine()


def start_vm(host, domain_name):
    '''
    Start a Virtual Machine.

    Args:
        host (HostCBTM): Host where the VM will be located
        domain_name (string): Name of the VM
    '''
    try:
        conn = host.get_conn_info().conn
    except KeyError:
        host_name = host.get_name()
        print('Could not find connection for the intended rack:', host_name)
        raise

    dom = conn.lookupByName(domain_name)
    if not dom.isActive():
        dom.create()


def shutdown_vm(host, domain_name):
    '''
    Shutdown a Virtual Machine.

    Args:
        host (HostCBTM): Host where the VM will be located
        domain_name (string): Name of the VM
    '''
    try:
        conn = host.get_conn_info().conn
    except KeyError:
        host_name = host.get_name()
        print('Could not find connection for the intended rack:', host_name)
        raise

    dom = conn.lookupByName(domain_name)
    if dom.isActive():
        dom.shutdownFlags(2)


def restart_vm(host, domain_name):
    '''
    Restart a Virtual Machine.

    Args:
        host (HostCBTM): Host where the VM will be located
        domain_name (string): Name of the VM
    '''
    try:
        conn = host.get_conn_info().conn
    except KeyError:
        host_name = host.get_name()
        print('Could not find connection for the intended rack:', host_name)
        raise

    dom = conn.lookupByName(domain_name)
    if dom.isActive():
        dom.reboot(2)


def copy_image(target, new_name, host):
    '''
    Copy VM's image.

    Args:
        target (string): Image to be copied
        new_name (string): Name for the new image
        host (HostCBTM): Host where the VM will be located
    '''
    storage_pool_target = POOL_NAME  # storage pool where are the templates.
    storage_pool_new = POOL_NAME
    template_name = 'volume_template_clone.xml'

    try:
        conn = host.get_conn_info().conn
    except Exception:
        print 'Could not find connection for the intended rack:', \
            host.get_name()
        raise

    s_pool_targ = conn.storagePoolLookupByName(storage_pool_target)
    s_pool_new = conn.storagePoolLookupByName(storage_pool_new)

    pathTemplate = DIR_NAME + template_name

    vol_XML = read_xml(pathTemplate)
    vol_XML = vol_XML \
        .replace('${VOL_NAME}', new_name) \
        .replace('${POOL_PATH}', get_pool_path(host))
    # path for the images in the racks

    try:
        orig_vol = s_pool_targ.storageVolLookupByName(target + '.img')
    except Exception:
        print 'Error: Cannot locate volume to be cloned.'
        exit(1)

    try:
        new_vol = s_pool_new.createXMLFrom(vol_XML, orig_vol, 0)
    except Exception:
        print 'Error copying the image.'
        exit(1)


def del_image(name, host):
    '''
    Delete VM's image.

    Args:
        name (string): Name of the image
        host (HostCBTM): Host where the VM will be located
    '''
    storage_pool = POOL_NAME

    try:
        conn = host.get_conn_info().conn
    except KeyError:
        print 'Could not find connection for the intended rack:', \
            host.get_name()
        raise

    try:
        s_pool = conn.storagePoolLookupByName(storage_pool)
    except Exception:
        print 'Error: Cannot locate Storage Pool.'

    if not s_pool.isActive():
        s_pool.create()

    try:
        vol = s_pool.storageVolLookupByName(name + '.img')
    except Exception:
        print 'Error: The volume doesn\'t exist.'
    else:
        # vol.wipe(0)
        vol.delete(0)

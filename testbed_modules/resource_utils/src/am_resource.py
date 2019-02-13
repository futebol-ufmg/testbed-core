# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------
# Copyright (c) 2011-2015 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
# ----------------------------------------------------------------------

from __future__ import absolute_import

import uuid
from gcf import geni
from resource import Resource


class AM_Resource(Resource):
    """ A Resource has an id, a type, and a boolean indicating availability.
    """

    STATUS_CONFIGURING = 'configuring'
    STATUS_READY = 'ready'
    STATUS_FAILED = 'failed'
    STATUS_UNKNOWN = 'unknown'
    STATUS_SHUTDOWN = 'shutdown'

    STATE_GENI_UNALLOCATED = 'geni_unallocated'
    STATE_GENI_ALLOCATED = 'geni_allocated'
    STATE_GENI_PROVISIONED = 'geni_provisioned'

    OPSTATE_GENI_PENDING_ALLOCATION = 'geni_pending_allocation'
    OPSTATE_GENI_NOT_READY = 'geni_notready'
    OPSTATE_GENI_CONFIGURING = 'geni_configuring'
    OPSTATE_GENI_STOPPING = 'geni_stopping'
    OPSTATE_GENI_READY = 'geni_ready'
    OPSTATE_GENI_READY_BUSY = 'geni_ready_busy'
    OPSTATE_GENI_FAILED = 'geni_failed'

    def __init__(self, rid, rtype):
        super(AM_Resource, self).__init__(rid, rtype)
        # self.id = rid
        # self.type = rtype
        self.available = True
        self.external_id = None
        # For V2 AMs
        self.status = AM_Resource.STATUS_UNKNOWN
        # For V3 AMs
        self.state = AM_Resource.STATE_GENI_UNALLOCATED
        self.operational_state = None
        self.ipaddress = None
        self.user_urn = None
        self.user_id = None
        self.reservation_id = None

    def factory(res_num, agg):
        if res_num > 60:
            return TelosB(agg, 'raw-telosb')
        if res_num > 50:
            return Container(agg, 'raw-wifi')
        if res_num > 30:
            return RaspberryPI(agg, 'raw-raspberry')
        if res_num > 10:
            return VirtualMachine(agg, 'usrp-vm')

    factory = staticmethod(factory)

    def urn(self, auth="geni//gpo//gcf"):
        publicid = 'IDN %s %s %s' % (auth, self.type, str(self.id))
        return geni.publicid_to_urn(publicid)

    def sliver_urn(self, auth="geni//gpo//gcf", sliver_id=uuid.uuid4()):
        # Used in SliverStatus
        publicid = 'IDN %s sliver %s%s-%s' % (auth, self.type,
                                              str(self.id), str(sliver_id))
        # If I knew that sliver_id was real, I'd do this:
        #        publicid = 'IDN %s sliver %s%s-%s' % (auth, str(sliver_id))
        return geni.publicid_to_urn(publicid)

    def toxml(self):
        template = ('<resource><urn>%s</urn><type>%s</type><id>%s</id>' +
                    '<available>%r</available></resource>')
        return template % (self.urn(), self.type, self.id, self.available)

    def __eq__(self, other):
        return self.id == other.id

    def __neq__(self, other):
        return self.id != other.id

    @classmethod
    def fromdom(cls, element):
        """Create a Resource instance from a DOM representation."""
        rtype = element.getElementsByTagName('type')[0].firstChild.data
        rid = int(element.getElementsByTagName('id')[0].firstChild.data)
        return Resource(rid, rtype)

    def deprovision(self):
        pass

    def reset(self):
        self.available = True
        self.state = AM_Resource.STATE_GENI_UNALLOCATED
        self.status = AM_Resource.STATUS_UNKNOWN
        self.operational_state = None


class VirtualMachine(AM_Resource):

    def __init__(self, agg, rtype):
        super(VirtualMachine, self).__init__(str(uuid.uuid4()), rtype)
        self._agg = agg
        self._img_type = None
        self._res_id = None

    def allocate(self):
        pass

    def deallocate(self):
        pass


class Container(AM_Resource):

    def __init__(self, agg, rtype):
        super(Container, self).__init__(str(uuid.uuid4()), rtype)
        self._agg = agg
        self._img_type = None
        self._res_id = None

    def allocate(self):
        pass

    def deallocate(self):
        pass


class TelosB(AM_Resource):

    def __init__(self, agg, rtype):
        super(TelosB, self).__init__(str(uuid.uuid4()), rtype)
        self._agg = agg
        self._img_type = None
        self._res_id = None

    def allocate(self):
        pass

    def deallocate(self):
        pass


class RaspberryPI(AM_Resource):

    def __init__(self, agg, rtype):
        super(RaspberryPI, self).__init__(str(uuid.uuid4()), rtype)
        self._agg = agg
        self._img_type = None
        self._res_id = None

    def allocate(self):
        pass

    def deallocate(self):
        pass

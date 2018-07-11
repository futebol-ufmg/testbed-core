#!/usr/bin/env python
"""
Copyright (c)  2016 The Provost, Fellows and Scholars of the
College of the Holy and Undivided Trinity of Queen Elizabeth near Dublin.
"""

from twisted.internet.protocol import Factory, Protocol
# from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, ssl


class ConnectionFactory(Factory):

    def __init__(self, handler):
        self.requests = {}
        self.handler = handler
        self.log = self.handler.operator.log

    def startFactory(self):
        self.log.debug('Starting Connection Factory')

    def stopFactory(self):
        self.log.debug('Stoping Connection Factory')

    def run_server(self, port):
        with open('../resources/cbtm_key.pem') as cbtm_key, \
                open('../resources/cbtm_cert.pem') as cbtm_cert:
            cert = ssl.PrivateCertificate.loadPEM(cbtm_key.read() +
                                                  cbtm_cert.read())
        with open('../resources/cbtm_cert.pem') as cbtm_cert:
            cert_auth = ssl.Certificate.loadPEM(cbtm_cert.read())
        reactor.listenSSL(port, self, cert.options(cert_auth))
        reactor.run()

    def buildProtocol(self, addr):
        return CBTProtocol(self.handler, self.log)


class CBTProtocol(Protocol):

    def __init__(self, pointer, log):
        self.handler = pointer
        self.log = log

    def send_response(self, msg):
        '''
            Receive messages from the Handler and send it back to the client.
        '''
        self.log.debug('Sending: "%s" to %s' % (msg, str(self.peer)))
        self.transport.write(msg)
        self.transport.loseConnection()

    def connectionMade(self):
        '''
            Capture connections to the server.
        '''
        self.peer = self.transport.getPeer()
        self.log.debug('New connection from %s' % str(self.peer))

    def dataReceived(self, rx_data):
        '''
            Receive data from the client and send it to the Handler.
        '''
        data = rx_data.strip()
        # self.log.debug('Received "%s" from %s'%(data, str(self.peer)))

        args = data.split(':')
        command = args.pop(0)

        msg = self.handler.handle(command, args)
        self.send_response(msg)

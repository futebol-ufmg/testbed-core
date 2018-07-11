import socket
import json
import base64
import zlib


class ResourceMonitor(object):

    def __init__(self):
        self.host = '127.0.0.1'
        # Frontend IP
        self.port = 4000
        self.request = 'HM:gr'
        self.resources = {}

    def send_health_request(self, msg):
        """
            Implements communication between the Coordinator and the CBTM,
            using the CBTProtocol.

            Args:
                msg (string): Command to be send to the CBTm server.

            PReturns:
                received (string): Response from the CBTm server.
        """
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # Connect to server and send data
            sock.connect((self.host, self.port))
            sock.sendall(msg + "\n")
            # Receive data from the server and shut down
            length = int(sock.recv(3))
            received = sock.recv(length)
            msg = str(zlib.decompress(base64.b64decode(received)))
        except Exception as e:
            raise e
        finally:
            sock.close()
        return msg

    def update(self):
        try:
            msg = self.send_health_request(self.request)
            hosts = json.loads(msg)
            self.resources = hosts
        except Exception as e:
            print('ERROR: ' + str(e))

    def get_resources(self):
        return self.resources


if __name__ == '__main__':
    try:
        rm = ResourceMonitor()
        while True:
            request = ''
            request = raw_input('Enter request: ')
            rm.request = 'HM:' + request
            msg = rm.update()

            print(str(rm.get_resources()))
    except KeyboardInterrupt:
        print('\nFinishing')
    except Exception as e:
        print('ERROR: ' + str(e))

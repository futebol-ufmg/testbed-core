from node import Node

class NodeCBTM(Node):

    def __init__(self, node_id, hardware, image, images, usb, raw, host):
        super(NodeCBTM, self).__init__(node_id,hardware,image,images,usb,raw)
        self.host = host

    def get_host(self):
        return self.host

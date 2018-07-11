from node import Node

class CBTMNode(Node):

	def __init__(self, log):
		super(CBTMNode, self).__init__(log)
		log.debug("Creating a New CBTM Node\n")

    # def __init__(self, node_id, hardware, image, images, usb, raw, host):
    #     super(NodeCBTM, self).__init__(node_id,hardware,image,images,usb,raw)
    #     self.host = host

    # def get_host(self):
    #     return self.host

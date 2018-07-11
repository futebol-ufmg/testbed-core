from resource import Resource

class OpenFlowSwitch(Resource):
    def __init__(self, log, res_num, basic_id):
        super(OpenFlowSwitch, self).__init__(log, res_num, basic_id)

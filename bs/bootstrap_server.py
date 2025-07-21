# Bootstrap server logic
class BootstrapServer:
    def __init__(self):
        self.nodes = {}
    def register_node(self, node_id, address):
        self.nodes[node_id] = address
    def get_nodes(self):
        return self.nodes

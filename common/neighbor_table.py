# Neighbor table utility
class NeighborTable:
    def __init__(self):
        self.neighbors = {}
    def add_neighbor(self, node_id, address):
        self.neighbors[node_id] = address
    def get_neighbors(self):
        return self.neighbors

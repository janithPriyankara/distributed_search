# Routing table utility
class RoutingTable:
    def __init__(self):
        self.routes = {}
    def add_route(self, dest, next_hop):
        self.routes[dest] = next_hop
    def get_routes(self):
        return self.routes

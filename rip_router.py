from sim.api import *
from sim.basics import *

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    def __init__(self):
        self.distances = {}
        #shortest distances keyed by destination
        #this gets exported directly
        #needs to be maintained with each state update

        self.vias = {}
        #neighbors keyed by destination
        #needs to be maintained with each state update

        self.ports = {}
        #port numbers keyed by neighbor

        self.state = {}
        #distance vectors keyed by neighbor
        #state[via][dest] gives distance

    def handle_rx (self, packet, port):
        if packet.__class__.__name__ == "DiscoveryPacket":
        	if packet.is_link_up:
        		self.distances[packet.src] = 1
        		self.state[packet.src] = {packet.src:1}
        		self.ports[packet.src] = port
        		self.vias[packet.src] = packet.src

        		self.update_vectors()

        	else:
        		del self.distances[packet.src]
        		del self.vias[packet.src]
        		del self.state[packet.src]
        		del self.ports[packet.src]

        		self.update_vectors()

        		#updateMessage = RoutingUpdate()
        		#RoutingUpdate.paths = distances
        		#send(updateMessage, port, true)
        elif packet.__class.__name__ == "RoutingUpdate":
        	self.state[packet.src] = packet.paths
        	self.state[packet.src][packet.src]=1 #distance vector might not include the source itself
        	if self.name in state:
				del self.state[self.name] #this entry is extraneous
        	self.update_vectors()
        else:
        	send(packet, ports[vias[packet.dst]], False)

    def update_vectors (self):
    	#state table has changed, update vias and distances
    	changes_made = False
    	for neighbor in self.state.keys():
    		for destination in self.state[neighbor].keys():
    			if self.state[neighbor][destination] < self.distances[destination] or \
    			   (self.state[neighbor][destination] == self.distances[destination] and \
    				self.ports[neighbor] < self.ports[self.vias[destination]]):
    				self.distances[destination] = self.neighbor_vector[destination]
    				self.vias[destination] = neighbor
    				changes_made = True

    	if changes_made:
    		for neighbor in ports:
    			paths = self.distances.copy()

    			for destination in self.vias.keys():
    				if self.vias[destination] == neighbor:
    					del self.paths[destination]

    			updatePacket = RoutingUpdate()
    			RoutingUpdate.paths = paths
    			send(updatePacket, self.ports[neighbor], False)

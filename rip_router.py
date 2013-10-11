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
        if isinstance(packet, DiscoveryPacket):
            print self.name + " received a discovery packet from " + str(packet.src)
            if packet.is_link_up:
                self.state[packet.src] = {packet.src:1}
                self.ports[packet.src] = port
                self.update_vectors()

            else:
                del self.distances[packet.src]
                del self.state[packet.src]
                del self.ports[packet.src]
                del self.vias[packet.src]
                for destination in self.vias.copy():
                    if self.vias[destination] == packet.src:
                        del self.vias[destination]
                        del self.distances[destination]
                for neighbor in self.state:
                    if packet.src in self.state[neighbor]:
                        del self.state[neighbor][packet.src]
                print "Distances: " + str(self.distances)
                print "State: " + str(self.state)
   
                self.update_vectors(True, updateSource = packet.src)

            #print "New distances: " + str(self.distances)

        elif isinstance(packet, RoutingUpdate):
            print self.name + " received a routing update packet from " + str(packet.src) + "..."
            #print "Routing packet contents: " + str(packet.paths)
            if packet.src not in self.distances:
                print "Dropping RoutingUpdate packet at " + self.name + ": Not connected to packet source"
            else:
                print "Processing routing update packet from " + str(packet.src)
                self.state[packet.src] = packet.paths
                for destination in self.state[packet.src].copy():
                    self.state[packet.src][destination]+=1
                self.state[packet.src][packet.src]=1 #distance vector might not include the source itself
                if self.__repr__() in self.state:
                    del self.state[self.name] #state doesn't need path to self
                self.update_vectors()


            #print "New distances: " + str(self.distances)

        else:
            print self.name + " received a data packet from " + str(packet.src)
            #print "Ports dictionary: " + str(self.ports) + "\n"
            #print "Vias dictionary: " + str(self.vias) + "\n"
            if packet.dst in self.distances:
                self.send(packet, self.ports[self.vias[packet.dst]], False)
            else:
                print "Dropping packet at " + self.name + "! "
                print str(packet.dst) + " seems unreachable from here."

    def update_vectors (self, changes_made = False, updateSource = None):
        #state table has changed, update vias and distances
        #print "Updating vectors. State dict: " + str(self.state)
        for destination in self.vias.copy():
            if destination not in self.state[self.vias[destination]]:
                del self.vias[destination]
                del self.distances[destination]
                changes_made = True

        for neighbor in self.state:
            for destination in self.state[neighbor]:
                #print "State dictionary: " + str(self.state) + "\n"
                #print "Vias dictionary: " + str(self.vias) + "\n"
                #print "Ports dictionary: " + str(self.ports) + "\n"
                #print "Distances dictionary: " + str(self.distances) + "\n"

                if (destination not in self.distances) or \
                    self.state[neighbor][destination] < self.distances[destination] or \
                   (self.state[neighbor][destination] == self.distances[destination] and \
                    self.ports[neighbor] < self.ports[self.vias[destination]]):
                   #we have a new destination from a neighbor in state, or
                   #we have a faster neighbor for a destination, or
                   #we have a new neighbor for a destination with a lower port number

                    self.distances[destination] = self.state[neighbor][destination]
                    self.vias[destination] = neighbor
                    changes_made = True

        if changes_made:
            for neighbor in self.ports:
                if neighbor == updateSource:
                   continue
                tailored_paths = self.distances.copy()
                #print "tailored paths before tailoring: " + str(tailored_paths)

                for destination in self.vias.keys(): #poison reverse
                    if self.vias[destination] == neighbor:
                        del tailored_paths[destination]

                #print "tailored paths after tailoring: " + str(tailored_paths)
                updatePacket = RoutingUpdate()
                updatePacket.paths = tailored_paths
                self.send(updatePacket, self.ports[neighbor], False)
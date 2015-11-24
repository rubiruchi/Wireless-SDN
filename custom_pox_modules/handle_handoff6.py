from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_dpid
from pox.lib.util import str_to_bool
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import time

log = core.getLogger()
globalIPToDPID = {}
globalMacToDPID = {}
macsOfSwitches = {}
globalMacPortDPID = {}
class OurController(object):
    
    def __init__(self, *args):
        core.listen_to_dependencies(self);
        print ("in controller's init")
    
    def _handle_core_ComponentRegistered (self, event):
        print ("Controller registered")
        if event.name == "host_tracker":
            event.component.addListenerByName("HostEvent",self.__handle_host_tracker_HostEvent)
    
    def __handle_host_tracker_HostEvent (self, event):
        # ipAddresses = event.entry.ipAddrs
        # hostIP = str(next(iter(ipAddresses), "no-ip-found"))
        hostMac = str(event.entry.macaddr)
        switchDPID = dpid_to_str(event.entry.dpid)
        
        if event.join:
            print("Time: " + time.asctime(time.localtime(time.time())) + "\n")
            print("Join: Host with Mac: " + hostMac + " joined with switch of DPID: " + switchDPID)
            globalMacToDPID[hostMac] = switchDPID
            self.printGlobalMacToDPIDTable()
            print "\n"
        
        if event.leave:
            msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
            # iterate over all connected switches and delete all their flows
            for connection in core.openflow.connections: # _connections.values() before betta
                connection.send(msg)
                print("Clearing all flows from %s." % (dpid_to_str(connection.dpid),))
            # msg = of.ofp_flow_mod()
            # # msg.match.dl_dst = EthAddr("00:00:00:00:00:11")
            # msg.match.dl_dst = EthAddr(hostMac)
            # msg.command = of.OFPFC_DELETE
            # core.openflow.sendToDPID(str_to_dpid(switchDPID), msg)
            print("Time: " + time.asctime(time.localtime(time.time())) + "\n")
            print("Leave: Host with Mac: " + hostMac + " left the switch of DPID: " + switchDPID)  
            # globalMacToDPID[hostMac] = "no-switch"
            # self.printGlobalMacToDPIDTable()
            # print "\n"
          
        if event.move:
            new_dpid = dpid_to_str(event._new_dpid)
            if(switchDPID!=new_dpid):
                msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
                #msg.match.dl_dst = EthAddr(hostMac)
                # iterate over all connected switches and delete all their flows
                for connection in core.openflow.connections: # _connections.values() before betta
                    #if(dpid_to_str(connection.dpid) == switchDPID):
                    connection.send(msg)
                    print("Clearing all flows from %s." % (dpid_to_str(connection.dpid),))
                # msg = of.ofp_flow_mod()
                # msg.match.dl_dst = EthAddr(hostMac)
                # msg.command = of.OFPFC_DELETE
                # core.openflow.sendToDPID(str_to_dpid(switchDPID), msg)
                print("Time: " + time.asctime(time.localtime(time.time())) + "\n")
                print("Move: Host with Mac: " + hostMac + " moved from switch with DPID: " + switchDPID + " to: " + new_dpid)
                # globalMacToDPID[hostMac] = dpid_to_str(event._new_dpid)
                # self.printGlobalMacToDPIDTable()
                # print "\n"
                
                # msg = of.ofp_packet_out()           #instructing a switch to send a packet
                # msg.in_port = of.OFPP_NONE          #packet is generated at the controller, so no need to define the in_port
                # msg.data = of.opf                #it's an OpenFlow port-status message
                # action = of.ofp_action_output(port = of.OFPP_FLOOD) #determine an action that will flood to output ports
                # msg.actions.append(action)          #append action to the action bucket
                # core.openflow.sendToDPID(str_to_dpid(switchDPID), msg)
    
    def printGlobalMacToDPIDTable(self):
        print("globalMacToDPIDTable content: ")
        # for key,value in globalMacToDPID.items():
            # print key,value

class OFSwitch(object):
  
  def __init__ (self, connection):
    self.connection = connection
    connection.addListeners(self)
    self.macToPort = {} #table that associates MAC to switch PORT
    
  def _handle_PacketIn (self, event):
    #log.info("In _handle_PacketIn(): Packet has arrived!")
    dpid = event.dpid
    inport = event.port #get port from which the packet arrived
    packet = event.parsed   #get the parsed packet
    if packet.type == ethernet.LLDP_TYPE: # Ignore LLDP packets
      return
    
    # if str(packet.dst) in globalMacToDPID:
    #     if(dpid_to_str(dpid) != globalMacToDPID[str(packet.dst)]):
    #         print ("yay!")
    #         msg = of.ofp_packet_out()
    #         msg.in_port = of.OFPP_NONE
    #         msg.data = packet
    #         core.openflow.sendToDPID(str_to_dpid(globalMacToDPID[str(packet.dst)]), msg)

    # use this method when flooding is necessary
    def flood():
        
        msg = of.ofp_packet_out()           #instructing a switch to send a packet
        msg.in_port = of.OFPP_NONE          #packet is generated at the controller, so no need to define the in_port
        msg.data = event.ofp                #it's an OpenFlow port-status message
        action = of.ofp_action_output(port = of.OFPP_FLOOD) #determine an action that will flood to output ports
        msg.actions.append(action)          #append action to the action bucket
        self.connection.send(msg.pack())    #pack the message in a sequence of bytes so that it can be sent over network
    
    #use this method when instructing the switches to drop the packet rather than
    #creating entry for it
    # def drop():
        
    print str(packet.payload)
    # if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        # print("LLDP packet received")
        # return
    # else:
    
    self.macToPort[packet.src] = inport     #add the Port in the table corresponding to the MAC given by packet.src
        
    
    
    #if the destination MAC is not in the table, flood!
    if packet.dst not in self.macToPort:
        flood()
        print("flooding")
        print ("Source: " + str(packet.src))
        print ("Destination: " + str(packet.dst))
        
        print("Mac To Port table content of DPID: " + dpid_to_str(dpid))
        for key,value in self.macToPort.items():
            print key,value
        print "\n"
    #else get the port corresponding to the MAC address and send the message to that port
    else:
        print("not-flooding")
        print ("Source: " + str(packet.src))
        print ("Destination: " + str(packet.dst))
        
        print("Mac To Port table content of DPID: " + dpid_to_str(dpid))
        for key,value in self.macToPort.items():
            print key,value
        print "\n"
        output_port = self.macToPort[packet.dst]    #get the port from the table
        
        # print "source: "
        # print packet.src
        # print " destination: "
        # print packet.dst
        
        
        #instructing the switch to create a flow table entry.
        #the flow table entry matches some fields of incoming packets, and executes some list of actions on matching packets
        msg = of.ofp_flow_mod()

        #match packet header fields defined by the 'packet' instance with the in_port attribute defined by inport
        # msg.match = of.ofp_match.from_packet(packet, inport)
        msg.match = of.ofp_match(in_port = inport, dl_dst = packet.dst)
        
        #append action to the action bucket that will send the message on the port defined by output_port
        msg.actions.append(of.ofp_action_output(port=output_port))
        
        msg.data = event.ofp    #it's an OpenFlow port-status message
        self.connection.send(msg.pack())    #pack the message in a sequence of bytes so that it can be sent over network
        
        
    #if the source mac address belongs to one of the mac addresses of the port
    #then don't add to the global MAC-PORT_DPID dictionary
    # listOfMacsForTheCurrentSwitch = macsOfSwitches[dpid_to_str(event.dpid)]
    # for Mac in listOfMacsForTheCurrentSwitch:
    #     if(str(packet.src) == str(Mac)):
    #         # print(str(packet.src) + " is one of Switch's MAC ID. Don't add!")
    #     else:
    #         # print(str(packet.src) + " is a host's MAC ID. Add to the globalMacPortDPID table!")
    #         globalMacPortDPID[str(packet.src)] = inport
    #         
    # print("globalMacPortDPID content:")
    # for key,value in globalMacPor./pox.py handle_handoff_6 host_tracker startup flow_stats > dump.textDPID.items():
    #     # print key,value
    # print "\n"
        

def switch_connected(event):
    # event.connection - connection object
    print ("Switch with DPID " + dpid_to_str(event.dpid) + " got connected")
    #print ("This switch has " + str(event.connection.features))
    ports = event.connection.features.ports
    
    # for port in ports:
    #     #format dict.setdefault(key, []).append(value)
    #     macsOfSwitches.setdefault(dpid_to_str(event.dpid), []).append(str(port.hw_addr))
    
    # print("Macs of switches content:")
    # for key,value in macsOfSwitches.items():
    #     # print key,value
    # print "\n"

    of_switch = OFSwitch(event.connection)  #creating instance of OFSwitch which corresponds to individual switches of the topology    
    
def callWhenAllSwitchesConnected():
    core.registerNew(OurController) #registering the controller component
    
    
def launch():
    core.openflow.addListenerByName("ConnectionUp", switch_connected)   #setting up listener for the event when the switches get connected
    #core.callDelayed(1, callWhenAllSwitchesConnected)
    core.registerNew(OurController) #registering the controller component
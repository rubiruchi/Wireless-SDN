#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""
import sys
import os

import mininet.net
import mininet.node
import mininet.cli
import mininet.log
import mininet.ns3

from mininet.net import Mininet, MininetWithControlNet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.ns3 import *

import ns.core
import ns.network
import ns.wifi
import ns.csma
import ns.wimax
import ns.uan
import ns.netanim

from mininet.opennet import *

"""
nodes is a list of node descriptions, each description contains several node attributes.

name: The node identifier.
type: The character of this node, can be host or switch.

position: The position of this node.
velocity: The velocity of this node, which will be used in host mobility model.
          The default mobility model is ns3::ConstantVelocityMobilityModel.

mobility: The mobility model of this node. setListPoritionAllocate() will take two parameters,
          MobilityHelper and ListPositionAllocate. After install the PositionAllocate in the
          MobilityHelper, setListoritionAllocate() will return the MobilityHelper.
"""

nodes = [   { 'name': 'h1', 'type': 'host', 'ip': '10.10.10.1', 'mac': '00:00:00:00:00:11', 'velocity': (7, 0, 0), 'position': (-180.0, 		         135.0, 0.0) },
            { 'name': 'h2', 'type': 'host', 'ip': '10.10.10.2', 'mac': '00:00:00:00:00:22', 'velocity': (0, 0, 0), 'position': (10.0,   		 		-135.0, 0.0) },
            { 'name': 's1', 'type': 'switch', 'position': (0.0, -100.0, 0.0) },
            { 'name': 's2', 'type': 'switch', 'position': (160.0, 90.0, 0.0) },
            { 'name': 's3', 'type': 'switch', 'position': (-160.0,90.0, 0.0) },
          

        ]

"""
wifiintfs is a list of wifi interface descriptions, each description contains some wifi attributes.
"""

wifiintfs = [ {'nodename': 'h1', 'type': 'sta', 'channel': 1, 'ssid': 'ssid'},
              {'nodename': 'h2', 'type': 'sta', 'channel': 11, 'ssid': 'ssid'},
              {'nodename': 's1', 'type': 'ap', 'channel': 1, 'ssid': 'ssid'},
              {'nodename': 's2', 'type': 'ap', 'channel': 6, 'ssid': 'ssid'},
              {'nodename': 's3', 'type': 'ap', 'channel': 11, 'ssid': 'ssid'},
              
           ]

"""
links is a list of Ethernet links.
"""

links = [ {'nodename1': 's1', 'nodename2': 's2'},
          {'nodename1': 's1', 'nodename2': 's3'},
          
       ]

def WifiNet():

    """ Create an Wifi network and add nodes to it. """

    net = Mininet()

    info( '*** Adding controller\n' )
    net.addController( 'c0', controller=RemoteController, ip='127.0.0.1', port=6633 )

    """ Initialize the WifiSegment, please refer ns3.py """
    wifi = WifiSegment(standard = ns.wifi.WIFI_PHY_STANDARD_80211g)
    wifinodes = []

    """ Initialize nodes """
    for n in nodes:

        """ Get attributes """
        nodename = n.get('name', None)
        nodetype = n.get('type', None)
        nodemob = n.get('mobility', None)
        nodepos = n.get('position', None)
        nodevel = n.get('velocity', None)
        nodeip = n.get('ip', None)
        nodemac = n.get('mac', None)

        """ Assign the addfunc, please refer Mininet for more details about addHost and addSwitch """
        if nodetype is 'host':
            addfunc = net.addHost
        elif nodetype is 'switch':
            addfunc = net.addSwitch
        else:
            addfunc = None
        if nodename is None or addfunc is None:
            continue

        """ Add the node into Mininet """
        node = addfunc (nodename, ip=nodeip, mac=nodemac)

        """ Set the mobility model """
        mininet.ns3.setMobilityModel (node, nodemob)
        if nodepos is not None:
            mininet.ns3.setPosition (node, nodepos[0], nodepos[1], nodepos[2])
        if nodevel is not None:
            mininet.ns3.setVelocity (node, nodevel[0], nodevel[1], nodevel[2])

        """ Append the node into wifinodes """
        wifinodes.append (node)

    """ Initialize Wifi Interfaces """
    for wi in wifiintfs:

        """ Get attributes """
        winodename = wi.get('nodename', None)
        witype = wi.get('type', None)
        wichannel = wi.get('channel', None)
        wissid = wi.get('ssid', None)

        """ Assign the addfunc, please refer the WifiSegment in ns3.py """
        if witype is 'sta':
            addfunc = wifi.addSta
        elif witype is 'ap':
            addfunc = wifi.addAp
        else:
            addfunc = None
        if winodename is None or addfunc is None or wichannel is None:
            continue

        """ Get wifi node and add it to the TapBridge """
        node = getWifiNode (wifinodes, winodename)
        addfunc (node, wichannel, wissid)

    """ Initialize Ehternet links between switches """
    for cl in links:
        clnodename1 = cl.get('nodename1', None)
        clnodename2 = cl.get('nodename2', None)
        if clnodename1 is None or clnodename2 is None:
            continue
        clnode1 = getWifiNode (wifinodes, clnodename1)
        clnode2 = getWifiNode (wifinodes, clnodename2)
        if clnode1 is None or clnode2 is None:
            continue
        CSMALink( clnode1, clnode2 )

    """ Enable Pcap output"""
    
    
    pcap = Pcap()
    pcap.setCSMAPath("/tmp/wifiroaminglogs/csma")
    pcap.setWifiPath("/tmp/wifiroaminglogs/wifi")
    info(pcap.enable())
    print pcap

    """ Enable netanim output"""
    anim = Netanim("/tmp/xml/wifi-wired-bridged4.xml", nodes)
    print anim

    """ Update node descriptions in the netanim """
    for node in wifinodes:
        anim.UpdateNodeDescription (node.nsNode, str(node) + '-' + str(node.nsNode.GetId()))
        if isinstance(node, mininet.node.OVSSwitch):
            color = (0, 255, 0)
        elif isinstance(node, mininet.node.Host):
            color = (0, 0, 255)
        anim.UpdateNodeColor (node.nsNode, color[0], color[1], color[2])

    """ Start the simulation """
    info( '*** Starting network\n' )
    net.start()
    mininet.ns3.start()
    info('PCAP CSMA PATH:')
    info(pcap.getCSMAPath())
    pcap.setCSMAPath("/tmp/wifiroaminglogs")
    info(pcap.getCSMAPath())
    info( 'Testing network connectivity\n' )
    wifinodes[1].cmdPrint( 'ping 10.10.10.1 -c 100' )

    CLI( net )

    info( '*** Stopping network\n' )
    mininet.ns3.stop()
    info( '*** mininet.ns3.stop()\n' )
    mininet.ns3.clear()
    info( '*** mininet.ns3.clear()\n' )
    net.stop()
    info( '*** net.stop()\n' )

if __name__ == '__main__':
    setLogLevel( 'info' )
    WifiNet()

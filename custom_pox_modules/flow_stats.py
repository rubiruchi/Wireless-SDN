#!/usr/bin/python
# Copyright 2012 William Yu
# wyu@ateneo.edu
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX. If not, see <http://www.gnu.org/licenses/>.
#

"""
This is a demonstration file created to show how to obtain flow 
and port statistics from OpenFlow 1.0-enabled switches. The flow
statistics handler contains a summary of web-only traffic.
"""

# standard includes
from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
import time
import os

# include as part of the betta branch
from pox.openflow.of_json import *

log = core.getLogger()
try:
    os.remove('flow_stats.txt')
except OSError:
    pass
the_file = open('flow_stats.txt', 'a')

# handler for timer function that sends the requests to all the
# switches connected to the controller.
def _timer_func ():
  for connection in core.openflow._connections.values():
    connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
    # connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))
  log.debug("Sent %i flow/port stats request(s)", len(core.openflow._connections))
  # print >> the_file, "Sent " + len(core.openflow._connections) + " flow/port stats request(s)"
  
  # the_file.write("Sent " + len(core.openflow._connections) + " flow/port stats request(s)")

# handler to display flow statistics received in JSON format
# structure of event.stats is defined by ofp_flow_stats()
def _handle_flowstats_received (event):
  stats = flow_stats_to_list(event.stats)
  log.debug("FlowStatsReceived from %s: %s", 
    dpidToStr(event.connection.dpid), stats)
  # print >> the_file, "FlowStatsReceived from " + dpidToStr(event.connection.dpid) ": " + stats
  
  the_file.write("Time: " + time.asctime(time.localtime(time.time())) + "\n")
  the_file.write("FlowStatsReceived from " + dpidToStr(event.connection.dpid) + ": " + str(stats) + "\n\n")

  # for f in event.stats:
  #   if str(f.match.dl_dst) == "00:00:00:00:00:11":
  #     the_file.write("FlowStatsReceived from " + dpidToStr(event.connection.dpid) + ": " + str(f.match.dl_dst) + "\n")
  #   else:
  #     the_file.write("Mac removed from flow table" + "\n\n")
  
  # Get number of bytes/packets in flows for web traffic only
  web_bytes = 0
  web_flows = 0
  web_packet = 0
  for f in event.stats:
    if f.match.tp_dst == 80 or f.match.tp_src == 80:
      web_bytes += f.byte_count
      web_packet += f.packet_count
      web_flows += 1
  log.info("Web traffic from %s: %s bytes (%s packets) over %s flows", 
    dpidToStr(event.connection.dpid), web_bytes, web_packet, web_flows)

# handler to display port statistics received in JSON format
def _handle_portstats_received (event):
  stats = flow_stats_to_list(event.stats)
  log.debug("PortStatsReceived from %s: %s", 
    dpidToStr(event.connection.dpid), stats)
  # print >> the_file, "FlowStatsReceived from " + dpidToStr(event.connection.dpid) ": " + stats
  # the_file.write("PortsStatsReceived from " + dpidToStr(event.connection.dpid) + ": " + str(stats))
    
# main functiont to launch the module
def launch ():
  from pox.lib.recoco import Timer
  # attach handsers to listners
  core.openflow.addListenerByName("FlowStatsReceived", 
    _handle_flowstats_received) 
  # core.openflow.addListenerByName("PortStatsReceived", _handle_portstats_received) 

  # timer set to execute every five seconds
  Timer(1, _timer_func, recurring=True)

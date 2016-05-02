from ryu.controller import ofp_event
import simple_switch_13
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import time

class detector(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(detector, self).__init__(*args, **kwargs)
        self.datapaths = {}
        hub.spawn(self.monitor)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def print_flow_stat(self, ev):
        print "=========="
        body = ev.msg.body
        for stat in body:
            print stat

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def print_port_stat(self, ev):
        print "switch id: %d" % ev.msg.datapath.id
        body = ev.msg.body
        print "received %d bytes" % body[0].rx_bytes

    #TODO: ask rules from each switches and initial rules here
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])    
    def state_change(self, ev):
        dp = ev.datapath
        self.datapaths[dp.id] = dp

    #TODO: another thread to check statistic
    def monitor(self):
        while True:
            time.sleep(3)
            dp = self.datapaths[1]
            ofproto = dp.ofproto
            parser = dp.ofproto_parser
            req = parser.OFPFlowStatsRequest(dp)
            dp.send_msg(req)
            """
            dp = self.datapaths[3]
            ofproto = dp.ofproto
            parser = dp.ofproto_parser
            req = parser.OFPPortStatsRequest(dp)
            dp.send_msg(req)
             """           
            """"
            for dp in self.datapaths.values():
                ofproto = dp.ofproto
                parser = dp.ofproto_parser
                req = parser.OFPPortStatsRequest(dp)
                dp.send_msg(req)
            
            """


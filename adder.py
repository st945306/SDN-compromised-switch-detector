'''
provide add rule functions
'''
from ryu.ofproto import inet
import topology

def addFWRuleByPort(datapath, tableID, inPort, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	match = parser.OFPMatch(in_port=inPort)
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		#priority=ofp.OFP_DEFAULT_PRIORITY,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addFWRuleByIP(datapath, tableID, ipDst, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=ipDst) #ip_proto=inet.IPPROTO_TCP)    
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addFWRuleByMatch(datapath, tableID, match, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		#priority=ofp.OFP_DEFAULT_PRIORITY,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addFWDefaultRule(datapath, tableID, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=None, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=0,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTRuleByPort(datapath, tableID, inPort, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	match = parser.OFPMatch(in_port=inPort)
	#print match
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		#priority=ofp.OFP_DEFAULT_PRIORITY,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTRuleByMatch(datapath, tableID, match, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTDefaultRule(datapath, tableID, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=None, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=0,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def removeRule(datapath, rule):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	mod = parser.OFPFlowMod(datapath=datapath, priority=rule.priority, match=rule.match, command=ofp.OFPFC_DELETE_STRICT,
							out_port=ofp.OFPP_ANY, out_group=ofp.OFPP_ANY)
	datapath.send_msg(mod)

def addTestRule(datapaths, path):
        for (switch, port) in path:
            print switch, port
            addFWRuleByIP(datapaths[switch], 0, '192.168.99.1', port)
	'''test by IP
	addFWRuleByIP(datapaths[1], 0, '10.0.0.3', 2)
	addFWRuleByIP(datapaths[2], 0, '10.0.0.3', 3)
	addFWRuleByIP(datapaths[3], 0, '10.0.0.3', 1)
	
	addFWRuleByIP(datapaths[2], 0, '192.168.0.1', 3)
	addFWRuleByIP(datapaths[3], 0, '192.168.0.1', 3)
	addFWRuleByIP(datapaths[4], 0, '192.168.0.1', 3)
        '''

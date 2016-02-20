'''
provide add rule functions
'''

def addFWRuleByPort(datapath, tableID, inPort, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	match = parser.OFPMatch(in_port=inPort)
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)
	
def addFWRuleByIP(datapath, tableID, ipDst, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	#eth_type is so important!!!
	match = parser.OFPMatch(eth_type=0x0800, ipv4_dst=ipDst)    
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTRulebyPort(datapath, tableID, inPort, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	match = parser.OFPMatch(in_port=inPort)  
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTRulebyMatch(datapath, tableID, match, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addTestRule(datapaths):
	addFWRuleByIP(datapaths[2], 0, '192.168.0.1', 5)
	addFWRuleByPort(datapaths[3], 2, 100, 200)
	addGTRulebyPort(datapaths[3], 2, 5, 5)
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

def addFWRuleByMatch(datapath, tableID, match, outPort):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	actions = [datapath.ofproto_parser.OFPActionOutput(outPort)]
	insts = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=match, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		priority=ofp.OFP_DEFAULT_PRIORITY,
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
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTRuleByPort(datapath, tableID, inPort, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	match = parser.OFPMatch(in_port=inPort)  
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
		priority=ofp.OFP_DEFAULT_PRIORITY,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def addGTDefaultRule(datapath, tableID, dstTableID):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	insts = [parser.OFPInstructionGotoTable(dstTableID)]
	mod = parser.OFPFlowMod(
		datapath=datapath, table_id=tableID, match=None, cookie=0,
		command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
		#priority=ofp.OFP_DEFAULT_PRIORITY,
		priority=1,
		flags=ofp.OFPFF_SEND_FLOW_REM, instructions=insts)
	datapath.send_msg(mod)

def removeRule(datapath, rule):
	ofp = datapath.ofproto
	parser = datapath.ofproto_parser
	mod = parser.OFPFlowMod(datapath=datapath, priority=rule.priority, match=rule.match, command=ofp.OFPFC_DELETE_STRICT,
							out_port=ofp.OFPP_ANY, out_group=ofp.OFPP_ANY)
	datapath.send_msg(mod)

def addTestRule(datapaths):
	addFWRuleByPort(datapaths[1], 0, 1, 2)
	#addFWRuleByPort(datapaths[1], 0, 2, 1)

	addFWRuleByPort(datapaths[2], 0, 2, 3)
	#addFWRuleByPort(datapaths[2], 0, 3, 2)

	addFWRuleByPort(datapaths[3], 0, 2, 1)
	#addFWRuleByPort(datapaths[3], 0, 1, 2)

	#addGTDefaultRule(datapaths[1], 3, 252)
	#addFWRuleByPort(datapaths[3], 2, 100, 200)
	#addGTRulebyPort(datapaths[3], 2, 5, 5)
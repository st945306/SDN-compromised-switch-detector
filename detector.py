from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER ,DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import switches, api
from ryu.lib import hub
import adder
import topology as topo

class SimpleDetector(simple_switch_13.SimpleSwitch13):
	_CONTEXTS = {'switches': switches.Switches}	

	def __init__(self, *args, **kwargs):
		super(SimpleDetector, self).__init__(*args, **kwargs)
		self.switches = kwargs['switches']
		#get dp from dpid
		self.datapaths = {}
		#check finish state of dpid
		self.finish = {}
		#topology[dpid][portNum] = (Connected switch)[dpid, portNum]
		self.topology = {}
		self.hosts = {}
		#original flow table on dpid
		self.flowTables = {}
		#counter flow tables
		self.counterTables = {}
		#check if counter table is ready
		self.ready = {}
		#max tableNum on dpid
		self.max_table = {}
		self.MAX_PORT = 16
		#malice value for dpid
		self.mValue = {}

		#init
		for i in range(1, topo.switchNum + 1):
			self.finish[i] = False
			self.counterTables[i] = {}
			self.ready[i] = 0
			self.mValue[i] = 0

		self.monitor_thread = hub.spawn(self._monitor)

	'''
	#request all flow tables from a switch
	def _request_stats(self, datapath):
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)
	'''
	#request specific flow table with table id
	def requestFlowTable(self, datapath, tableID):
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath, table_id=tableID)
		datapath.send_msg(req)

	#get max tableNum for each switch
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def _switch_features_handler(self, ev):
		msg = ev.msg
		self.max_table[msg.datapath_id] = msg.n_tables
		print 'max table num is %d' % msg.n_tables

	'''
	use this to record topology but switches.links is always empty?
	def _record_topology(self, dpid):
		hub.sleep(0.01)
		for link in self.switches.links:
			src = link.src
			dst = link.dst
			self.topology.setdefault(src.dpid, {})
			self.topology.setdefault(dst.dpid, {})
			self.topology[src.dpid][src.port_no] = [dst.dpid, dst.port_no]
			self.topology[dst.dpid][dst.port_no] = [src.dpid, src.port_no]
		self.hosts.setdefault(dpid, [])
		for port in self.switches.port_state[dpid]:
			if port <= self.MAX_PORT and not self.topology[dpid].has_key(port):
				self.hosts[dpid].append(port)
	'''
	#called when a switch is added
	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		datapath = ev.datapath
		dpid = datapath.id
		if ev.state == MAIN_DISPATCHER:
			if not dpid in self.datapaths:
				self.datapaths[dpid] = datapath
				#self._record_topology(dpid)
				if len(self.datapaths) == topo.switchNum:
					topo.initTopology(self.switches, self.max_table)
					adder.addTestRule(self.datapaths)
					#this should be change
					#self.requestFlowTable(self.datapaths[2], 0)
					
					for i in range(1, topo.switchNum + 1):
						self.requestFlowTable(self.datapaths[i], 0)
					
		#what is this for?
		else:
			if dpid in self.datapaths:
				del self.datapaths[dpid]
				del self.finish[dpid]
				for key,value in self.topology[dpid].items():
					del self.topology[value[0]][value[1]]
				del self.topology[dpid]
				del self.hosts[dpid]

	#return true if all switches finish initialize
	def isFinish(self):
		for i in range(1, topo.switchNum + 1):
			if not self.finish[i]:
				return False
		return True

	#return true if all counter tables for dpid is ready
	def isReady(self, dpid):
		adjSwitches = topo.getAdjSwitches(dpid)
		for i in adjSwitches:
			if self.ready[i] != 2:
				return False
		return True	

	#called when a switch reply flow table
	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		datapath = ev.msg.datapath
		dpid = datapath.id
		ofp = datapath.ofproto
		parser = datapath.ofproto_parser

		#add rule
		if not self.isFinish():
			#save the original flow table
			self.flowTables[dpid] = body
			#create default rules for every table on this switch
			for port in range(1, topo.maxPort[dpid] + 1):
				if topo.isSwitch(dpid, port):
					#add forwarding rule on toTable on this switch
					toTableID = topo.getToTableID(dpid, port)
					adder.addFWDefaultRule(self.datapaths[dpid], toTableID, port)
					#add goto main table rule on fromTable on this switch
					fromTableID = topo.getFromTableID(dpid, port)
					adder.addGTDefaultRule(self.datapaths[dpid], fromTableID, topo.getMainTableID(dpid))
					#add goto fromTable rule on t0
					adder.addGTRuleByPort(self.datapaths[dpid], 0, port, fromTableID)
			#add default rule on table 0, so packet from host won't ask controller
			adder.addGTDefaultRule(self.datapaths[dpid], 0, topo.getMainTableID(dpid))
			#process each rule
			for rule in body:
				print rule
				instruction = rule.instructions[0]
				#forward rule
				if isinstance(instruction, parser.OFPInstructionActions):
					forwardPort = rule.instructions[0].actions[0].port
					if not 1 <= forwardPort <= 255:
						continue
					for port in range(1, topo.maxPort[dpid] + 1):
						if topo.isSwitch(dpid, port):
							remoteSwitchID = topo.getRemoteSwitch(dpid, port)
							remotePort = topo.getRemotePort(dpid, port)
							#add forwarding rule on toTable on remote switch
							toTableID = topo.getToTableID(remoteSwitchID, remotePort)
							adder.addFWRuleByMatch(self.datapaths[remoteSwitchID], toTableID, rule.match, remotePort)
							#add goto main table rule on fromTable on remote switch
							fromTableID = topo.getFromTableID(remoteSwitchID, remotePort)
							adder.addGTRuleByMatch(self.datapaths[remoteSwitchID], fromTableID,
													rule.match, topo.getMainTableID(remoteSwitchID))
					#add goto toTable rule to main table on this switch
					mainTableID = topo.getMainTableID(dpid)
					forwardPort = rule.instructions[0].actions[0].port
					toTableID = topo.getToTableID(dpid, forwardPort)
					adder.addGTRuleByMatch(self.datapaths[dpid], mainTableID, rule.match, toTableID)
					#delete this rule on t0
					adder.removeRule(self.datapaths[dpid], rule)

				#goto table rule
				else:
					pass
			self.finish[dpid] = True
		#save table to check
		else:
			tableID = body[0].table_id
			self.counterTables[dpid][tableID] = body
			self.ready[dpid] += 1
			print 'table', tableID, 'on switch', dpid, 'is received'

	def compare(self, a, b):
		if "ipv4_dst" in a and "ipv4_dst" in b:
			return a['ipv4_dst'] == b['ipv4_dst']
		print "not ipv4 rules"
		return False

	def findRule(self, match, table):
		#print "match", match
		#print "table", table
		for rule in table:
			#print "match", match
			#print "rule.match", rule.match
			if self.compare(match, rule.match):
				return rule
		print "not found", match
	
	def sumAllCounters(self, table):
		result = 0
		for rule in table:
			result += rule.packet_count
		return result

	def check(self, dpid):
		datapath = self.datapaths[dpid]
		ofp = datapath.ofproto
		parser = datapath.ofproto_parser
		#this is the flowtable to check
		oriFlowtable = self.flowTables[dpid]
		for i in range(1, topo.switchNum + 1):
			self.ready[i] = 0
		for port in range(1, topo.maxPort[dpid] + 1):
			if topo.isSwitch(dpid, port):
				remoteSwitchID = topo.getRemoteSwitch(dpid, port)
				remotePort = topo.getRemotePort(dpid, port)
				#request toTable
				self.requestFlowTable(self.datapaths[remoteSwitchID],
										topo.getToTableID(remoteSwitchID, remotePort))
				#request fromTable
				self.requestFlowTable(self.datapaths[remoteSwitchID], 
										topo.getFromTableID(remoteSwitchID, remotePort))
				print 'request send'
		#check if all counter tables are ready
		while not self.isReady(dpid):
			print 'not ready'
			hub.sleep(1)
			
		print 'ready to check'
		for rule in oriFlowtable:
			match = rule.match
			instruction = rule.instructions[0]

			#forward rule
			if isinstance(instruction, parser.OFPInstructionActions):
				forwardPort = instruction.actions[0].port
				#ignore broadcast rule
				if forwardPort > topo.maxPort[dpid]:
					continue
				#get the sum of in-packet
				inPacket = 0
				if "in_port" in rule.match:
				#match field is port
					inPort = rule.match["in_port"]
					remoteSwitchID = topo.getRemoteSwitch(dpid, inPort)
					remotePort = topo.getRemotePort(dpid, port)
					toTableID = topo.getToTableID(remoteSwitchID, remotePort)
					inPacket = self.sumAllCounters(self.counterTables[remoteSwitchID][toTableID])
				elif "ipv4_dst" in rule.match:
				#match field is ipv4
					for port in range(1, topo.maxPort[dpid] + 1):
						if topo.isSwitch(dpid, port):
							remoteSwitchID = topo.getRemoteSwitch(dpid, port)
							remotePort = topo.getRemotePort(dpid, port)
							toTableID = topo.getToTableID(remoteSwitchID, remotePort)
							counterRule = self.findRule(match, self.counterTables[remoteSwitchID][toTableID])
							print counterRule.packet_count, "packets from switch", remoteSwitchID
							inPacket += counterRule.packet_count

				print "sum of in-packet:", inPacket
				
				'''
				#get the sum of out-packet (real)
				remoteSwitchID = topo.getRemoteSwitch(dpid, forwardPort)
				remotePort = topo.getRemotePort(dpid, forwardPort)
				fromTableID = topo.getFromTableID(remoteSwitchID, remotePort)
				counterRule = self.findRule(match, self.counterTables[remoteSwitchID][fromTableID])
				outPacket = counterRule.packet_count
				'''
				#get the sum of out-packet (fake)
				remoteSwitchID = topo.getRemoteSwitch(dpid, forwardPort)
				remotePort = topo.getRemotePort(dpid, forwardPort)
				fromTableID = topo.getFromTableID(remoteSwitchID, remotePort)
				outPacket = self.sumAllCounters(self.counterTables[remoteSwitchID][fromTableID])
				print "out-packet:", outPacket



		'''
			if rule.action == fowarding:
				dst_switch = table_B.action.out_dst
				sum = 0

				#count the sum of in-packet
				for all injacent switch of B except dst_switch:
					get their to_B table
					for t in all to_B tables:
						for rules r in table t:
							if r.match_field == match:
								sum += counter

				#
				for all rules r in dst_switch.from_B table:
					if r.match_field == match:
						if (r.counter == sum):
							this rule passed the test
						else:
							this rule failed the test
							#can break and assume this switch is compromised

			else if rule.action == dropping:
				for all injacent switches of B:
					get their from_B table
					for all table t in all from_B table:
						for all rules r in table t:
							if r.match_field == match:
								if counter != 0:
									boooo!
		'''
		return True
	
	
	def _monitor(self):
		#wait until all switches finish initailize
		while not self.isFinish():
			hub.sleep(1)

		#self.check(2)
		
		while True:
			for dp in self.datapaths.values():
				dpid = dp.id
				if dpid == 2 and self.check(2) == False:
					self.mValue[dpid] += 1			
			hub.sleep(10)
		
	'''
	#called when a switch send a flow table back
	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def _flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		datapath = ev.msg.datapath
		dpid = datapath.id
		ofproto = datapath.ofproto		
		parser = datapath.ofproto_parser

		#do the add rule part
		if not self.finish[dpid]:
			for rule in body:
				if rule.cookie == 1:
					continue
				cookie = 1
				flags = rule.flags
				hard_timeout = rule.hard_timeout
				idle_timeout = rule.idle_timeout
				match = rule.match
				priority = rule.priority
				table_id = rule.table_id

				instructions = []
				out_ports = []
				temp = []
				for instruction in rule.instructions:
					if isinstance(instruction, parser.OFPInstructionGotoTable):
						instructions.append(parser.OFPInstructionGotoTable(1+self.MAX_PORT+instruction.table_id))
					else:
						actions = []
						for action in instruction.actions:
							if isinstance(action, parser.OFPActionOutput) and action.port <= self.MAX_PORT:	
								out_ports.append(action.port)
								temp.append(parser.OFPInstructionGotoTable(self.max_table[dpid] - 1 - self.MAX_PORT + action.port))
							else:
								actions.append(action)
						if actions:
							instructions.append(parser.OFPInstructionActions(instruction.type, actions))
				instructions += temp
								
				# modify original rule
				mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, command=ofproto.OFPFC_DELETE_STRICT,
										out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPP_ANY)
				datapath.send_msg(mod)

				mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie, table_id=1+self.MAX_PORT+table_id, idle_timeout=idle_timeout,
										hard_timeout=hard_timeout, priority=priority, flags=flags, match=match, instructions=instructions)
				datapath.send_msg(mod)

				# add forwarding table
				for port in self.hosts[dpid]:
					# table 0
					match_0 = parser.OFPMatch(in_port=port)
					instruction = [parser.OFPInstructionGotoTable(port)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=0, match=match_0, instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)
					# add normal ingress table
					instruction = [parser.OFPInstructionGotoTable(1+self.MAX_PORT)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=port, match=match_0, instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)
					# add normal egerss table
					match_0 = parser.OFPMatch()
					actions = actions = [parser.OFPActionOutput(port)]
					instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=self.max_table[dpid]-1-self.MAX_PORT+port, match=match_0,
											instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)

				for port in self.topology[dpid].keys():
					# table 0
					match_0 = parser.OFPMatch(in_port=port)
					instruction = [parser.OFPInstructionGotoTable(port)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=0, match=match_0, instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)
					# add normal ingress table
					instruction = [parser.OFPInstructionGotoTable(1+self.MAX_PORT)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=port, match=match_0, instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)
					# add normal egerss table
					match_0 = parser.OFPMatch()
					actions = actions = [parser.OFPActionOutput(port)]
					instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
					mod = parser.OFPFlowMod(datapath=datapath, table_id=self.max_table[dpid]-1-self.MAX_PORT+port, match=match_0,
											instructions=instruction, priority=0, cookie=cookie)
					datapath.send_msg(mod)
				new_match = {}
				for key,value in match.items():
					if key != 'in_port':					
						new_match[key] = value
				# forwarding rule
				if len(instructions) != 0:					
					if len(out_ports) != 0:					
						for port,dp in self.topology[dpid].items():
							if new_match.has_key('in_port'):
								del new_match['in_port']
							match = parser.OFPMatch(**new_match)
							# ingress node
							if not port in out_ports:
								actions = [parser.OFPActionOutput(dp[1])]
								instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
								table_id = self.max_table[dp[0]] - 1 - self.MAX_PORT + dp[1]
								# add ingress rule
								mod = parser.OFPFlowMod(datapath=self.datapaths[dp[0]], cookie=cookie, table_id=table_id, idle_timeout=idle_timeout,
														hard_timeout=hard_timeout, priority=priority, flags=flags, match=match, instructions=instruction)
								self.datapaths[dp[0]].send_msg(mod)
								# add egress rule for invalid output port
								new_match['in_port'] = dp[1]
								match = parser.OFPMatch(**new_match)
								mod = parser.OFPFlowMod(datapath=self.datapaths[dp[0]], cookie=cookie, table_id=dp[1], idle_timeout=idle_timeout,
														hard_timeout=hard_timeout, priority=priority, flags=flags, match=match, instructions=[])
								self.datapaths[dp[0]].send_msg(mod)
							# egress node
							else:
								# add egress rule for true output port
								instruction = [parser.OFPInstructionGotoTable(1+self.MAX_PORT)]
								mod = parser.OFPFlowMod(datapath=self.datapaths[dp[0]], cookie=cookie, table_id=dp[1], idle_timeout=idle_timeout,
														hard_timeout=hard_timeout, priority=priority, flags=flags, match=match, instructions=instruction)
								self.datapaths[dp[0]].send_msg(mod)
				# drop rule
				else:
					for port,dp in self.topology[dpid].items():
						new_match['in_port'] = dp[1]
						match = parser.OFPMatch(**new_match)
						mod = parser.OFPFlowMod(datapath=self.datapaths[dp[0]], cookie=cookie, table_id=dp[1], idle_timeout=idle_timeout,
												hard_timeout=hard_timeout, priority=priority, flags=flags, match=match, instructions=[])
						self.datapaths[dp[0]].send_msg(mod)
			self.finish[dpid] = True
		#check counters return table
		else:
			#save all table in some data structure

	'''

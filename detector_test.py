from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER ,DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import switches
from ryu.lib import hub

class SimpleDetector(simple_switch_13.SimpleSwitch13):
	_CONTEXTS = {'switches': switches.Switches}	

	def __init__(self, *args, **kwargs):
		super(SimpleDetector, self).__init__(*args, **kwargs)
		self.switches = kwargs['switches']
		self.datapaths = {}
		self.finish = {}
		self.topology = {}
		self.hosts = {}
		self.max_table = {}
		self.MAX_PORT = 16
		
		#self.rating = {}
		#self.monitor_thread = hub.spawn(self._monitor)

	#request all flow tables from a switch
	def _request_stats(self, datapath):
		parser = datapath.ofproto_parser
		req = parser.OFPFlowStatsRequest(datapath)
		datapath.send_msg(req)

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def _switch_features_handler(self, ev):
		msg = ev.msg
		self.max_table[msg.datapath_id] = msg.n_tables

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

	#called when a switch is added
	@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
		datapath = ev.datapath
		dpid = datapath.id
		if ev.state == MAIN_DISPATCHER:
			if not dpid in self.datapaths:
				self.datapaths[dpid] = datapath
				self.finish[dpid] = False
				self._record_topology(dpid)
				self._request_stats(datapath)
		else:
			if dpid in self.datapaths:
				del self.datapaths[dpid]
				del self.finish[dpid]
				for key,value in self.topology[dpid].items():
					del self.topology[value[0]][value[1]]
				del self.topology[dpid]
				del self.hosts[dpid]

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

		'''
		#check counters return table
		else:
			save all table in some data structure

		'''
	'''
	def check(dp):
		self._request_stats(dp)	#this is the table B
		for all injacent switches:
			_request_stats(dp)	#request all counter tables from A, C, D

		###check if tables are ready
		while(not ready)
			hub.sleep(1)

		for all rules in table_B:
			match = rule.match_field
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
	def _monitor(self):
		'''
		while True:
			for dp in self.datapaths.values():
				dpid = dp.id
				if self.finish[dpid]:
					if check(dp) == fail:
						self.rating[dpid]++
				
			hub.sleep(10)


		'''

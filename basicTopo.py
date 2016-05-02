from mininet.topo import Topo
import imp

class basicTopo(Topo):
	def __init__(self):
		Topo.__init__(self)
		randTopo = imp.load_source('module.name', 'randTopo.py')
		switches = []
		'''
		for i in range(0, 6):
			s.append(self.addSwitch("s%d" % i))
			h.append(self.addHost("h%d" % i))
			self.addLink(s[i], h[i])

		self.addLink(s[0], s[1])
		self.addLink(s[0], s[4])
		self.addLink(s[1], s[2])
		self.addLink(s[1], s[5])
		self.addLink(s[3], s[1])
		self.addLink(s[3], s[4])
		self.addLink(s[4], s[2])
		self.addLink(s[4], s[5])
		'''
		for i in range(1, randTopo.switchNum + 1):
			switches.append(self.addSwitch("s%d" % i))

		record = {}
		for i, v in randTopo.portMap.iteritems():
			record[i] = 0
		for i, v in randTopo.portMap.iteritems():
			if v[0] == 0 or v[1] == 0:
				continue
			if record[i] == 1:
				continue
			print 'link from switch', i[0], 'port', i[1], 'to switch', v[0], 'port', v[1]
			self.addLink(switches[i[0] - 1], switches[v[0] - 1], port1 = i[1], port2 = v[1])
			record[v] = 1

topos = {"basicTopo": (lambda: basicTopo())}

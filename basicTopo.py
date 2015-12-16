from mininet.topo import Topo

class basicTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        s = []
        h = []

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

topos = {"basicTopo": (lambda: basicTopo())}

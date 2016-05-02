# SDN-compromised-switch-detector
###This is a detector for software-defined network.
###To open mininet:
*	sudo mn --controller remote --custom topoGen.py --topo basicTopo

###To set a switch s1 to OpenFlow protocol 1.3:
*	sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

###To run detector.py:
*	ryu-manager detector.py

'''
define topology for controller
'''
######define######
switchNum = 3

#portMap[(dpid, port)] = (dpid, port)
portMap = {}

#switch
portMap[(1, 2)] = (2, 2)
portMap[(2, 2)] = (1, 2)
portMap[(2, 3)] = (3, 2)
portMap[(3, 2)] = (2, 3)

#host
portMap[(1, 1)] = (0, 0)
portMap[(2, 1)] = (0, 0)
portMap[(3, 1)] = (0, 0)

######define######

maxPort = {}
maxTable = {}

def initTopology(switches, max_table):
	global maxTable
	global maxPort
	maxTable = max_table
	portState = switches.port_state
	for i in range(1, switchNum + 1):
		maxPort[i] = len(portState[i]) - 1
	print maxPort
	print getFromTableID(2, 2)

#get to_port_table ID on switch dpid
def getToTableID(dpid, port):
	return maxTable[dpid] - port

#get from_port_table ID on switch dpid
def getFromTableID(dpid, port):
	return port

def getMainTableID(dpid):
	return maxPort[dpid] + 1

def isSwitch(dpid, port):
	return portMap[(dpid, port)] != (0, 0)

#return a list of dpid of adjacent switches
def getAdjSwitches(dpid):
	result = []
	for port in range(1, maxPort[dpid] + 1):
		if isSwitch(dpid, port):
			result.append(getRemoteSwitch(dpid, port))
	return result

def getRemoteSwitch(dpid, port):
	return portMap[(dpid, port)][0]

def getRemotePort(dpid, port):
	return portMap[dpid, port][1]
'''
define topology for controller
'''
import randTopo
import random
######define######
switchNum = randTopo.switchNum

#portMap[(dpid, port)] = (dpid, port)
portMap = randTopo.portMap


######define######

maxPort = {}
maxPort[1] = 2
maxPort[2] = 3
maxPort[3] = 3
maxPort[4] = 3
maxPort[5] = 2

maxTable = {}

def initTopology(max_table):
	global maxTable
	global maxPort
	maxTable = max_table
	print "max port:", maxPort

#get to_port_table ID on switch dpid
def getToTableID(dpid, port):
	return maxTable[dpid] - port

#get from_port_table ID on switch dpid
def getFromTableID(dpid, port):
	return port

def getMainTableID(dpid):
	return maxPort[dpid] + 1

def isSwitch(dpid, port):
	return (dpid, port) in portMap

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

isUsed = {}
def findUnusedAdj(centerSwitch):
    candidate = []
    for i in range(1, 255):
        t = (centerSwitch, i)
        if t in portMap and portMap[t][0] not in isUsed:
            candidate.append(portMap[t])
    if len(candidate) == 0:
        print 'dead end'
        return (-1, -1)
    return random.choice(candidate)

def getPath(length):
    path = []
    thisSwitch = random.choice(portMap.keys())
    for i in range(1, length + 1):
        nextSwitch = findUnusedAdj(thisSwitch[0])
        path.append(portMap[nextSwitch])
        isUsed[thisSwitch[0]] = True
        thisSwitch = nextSwitch
    print path
    return path
    


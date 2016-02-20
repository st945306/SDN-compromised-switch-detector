'''
define topology for controller
'''

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
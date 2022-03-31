# Quantum SPICE 
# Converts circuit information to capacitance & inductance graph

# arbitrary class for each components in the quantum circuit

class circComp(object):

    circCompList = []

    def __init__(self, name, type, terminals, value, connections, subsystem=None):
        # name (string) -> e.g. C1, I2
        self.name = name
        # type (string) => e.g. capacitor, inductor
        self.type = type
        # terminal (string tuple) => e.g. (C1_1, C1_2)
        self.terminals = terminals
        # value (string) => e.g. 4F, 15H
        self.value = value
        # connection (dictionary w string key and string list value) 
        # e.g. {C1_1: [C2_1, I1_2], C1_2: []}
        # stores list of connections between 
        # self.terminals (key) & other terminals (values)
        # no connection is shown by []
        self.connections = connections
        self.subsystem = subsystem
        # add circComp instance to circCompList
        circComp.circCompList.append(self)      

    def __del__(self):
        self.name = None
        self.type = None
        self.terminals = None
        self.value = None
        self.connections = None
        self.subsystem = None
        del self 

class Subsystem(object):

    subSystemMap = []

    def __init__(self, name, sys_type, options):
        self.name = name
        self.sys_type = sys_type 
        self.options = options
        self.components = []
        self.nodes = []
        # add circComp instance to circCompList
        Subsystem.subSystemMap.append(self)  


# clear circuit
def clearCircCompList():
    for comp in circComp.circCompList:
        circComp.__del__(comp)
    circComp.circCompList = []

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
##              Helper Functions              ##
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# return the circComp that has the input terminal
def getCompFromTerminal(terminal):
    for comp in circComp.circCompList:
        if terminal in comp.terminals:
            return comp
    raise Exception(terminal + " terminal doesn't exist, perhaps you have a wrong test case?")

# return other terminal in the same component 
# (assume only two terminals in a single componenet)
def getOtherTermSameComp(terminal):
    comp = getCompFromTerminal(terminal)
    for t in comp.terminals:
        if (t != terminal):
            return t
    
# return the value of the comp that 
# the terminal is in
def getValFromTerminal(terminal):
    comp = getCompFromTerminal(terminal)
    return comp.value

def getCompFromName(name):
    for comp in circComp.circCompList:
        if comp.name == name:
            return comp
    raise Exception(comp + " comp doesn't exist")  

# convert string val to int
def valToInt(val):
    num = ''  
    for c in val:
        if c.isdigit():
            num += c
    return int(num)

# get capacitance and inductance of a junction
# as integers
def getJuncVal(val):
    split = val.split('_')
    cap = valToInt(split[0])  
    ind = valToInt(split[1])  
    return (int(cap), int(ind))

def getSet(term, cons):
    conSet = set()
    conSet.update(cons)
    conSet.add(term)
    conSet.discard('GND')
    # nodeDict's key is frozenset
    return frozenset(conSet)

# return node name if terminal is in nodeDict
# otherwise, return None
def tInDict(term, dict):
    for entry in dict:
        if term in entry:
            return dict[entry]
    return None

def nodeInList(node1, node2, nTups):
    if (node1, node2) in nTups or (node2, node1) in nTups:
        return True
    else: 
        return False

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
##              Main Functions              ##
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def convertParallel():
    # make 2d list of comps connected in parallel
    parallelConnections = []
    existingComp = []
    for comp in circComp.circCompList:
        if comp not in existingComp:
            conInParallel = [comp]
            connected1 = []
            for term in comp.connections:
                for con in comp.connections[term]:
                    # skip resonator and ground node 
                    if con[0] != 'R' and con != 'GND':
                        conComp = getCompFromTerminal(con)
                        # if same type, add in the same list 
                        if (comp.type == 'junction') or (conComp.type == comp.type) or (conComp.type == 'junction'):
                            # if same comp connected to both terminals
                            if conComp in connected1:
                                conInParallel.append(conComp)
                            else:
                                connected1.append(conComp)     
            if len(conInParallel) > 1:
                parallelConnections.append(conInParallel)
                for c in conInParallel:
                    existingComp.append(c)
    # loop through parallelConnections list,
    # replace parallel-conneted comps with single comp
    # don't remove junctions for now
    for con in parallelConnections:
        newCap = 0 
        newInd = 0

        # check if there's a junction
        hasJunction = False 
        junction = None
        for comp in con: 
            if (comp.type == 'junction'):
                hasJunction = True
                junction = comp

        # if there's a junction, add capacitance and inductance
        # of other parallel-connected components to the junction
        if hasJunction: 
            (newCap, newInd) = getJuncVal(junction.value)
            for comp in con:
                if (comp.name != junction.name):
                    # add capacitance and inductance in parallel
                    if comp.type == 'junction':
                        (cap, indu) = getJuncVal(comp.value)
                        newCap += cap
                        newInd +=  1 / indu
                    elif comp.type == 'capacitor':
                        newCap += valToInt(comp.value)
                    elif comp.type == 'inductor':
                        newInd += 1 / valToInt(comp.value)

                    # remove redundant connections
                    for t in comp.terminals:
                        for origT in junction.terminals:
                            if t in junction.connections[origT]:
                                junction.connections[origT].remove(t) 

                    # remove terminals of comp in all other comps' connections
                    for itComp in circComp.circCompList: 
                        for itT in itComp.terminals:
                            for compT in comp.terminals:
                                if compT in itComp.connections[itT]:
                                    itComp.connections[itT].remove(compT)

                    # remove parallel-connected component
                    circComp.circCompList.remove(comp)    

            # update capacitance and inductance of the junction  
            junction.value = str(newCap) + 'F_' + str(newInd) + 'H'
        # if there're only capacitors
        elif con[0].type == 'capacitor':       
            for comp in con[1:]:
                # add capacitance in parallel
                newVal += valToInt(comp.value)
                # remove redundant connections
                for t in comp.terminals:
                    for origT in con[0].terminals:
                        if t in con[0].connections[origT]:
                            con[0].connections[origT].remove(t) 
                # remove parallel-connected component
                circComp.circCompList.remove(comp)      
            con[0].value = str(newVal) + 'F'          
        # if there're only inductors
        elif con[0].type == 'inductor':
            for comp in con[1:]:
                # inverse -- 
                newVal +=  1 / valToInt(comp.value)
                # remove redundant connections
                for t in comp.terminals:
                    for origT in con[0].terminals:
                        if t in con[0].connections[origT]:
                            con[0].connections[origT].remove(t)  
                # remove parallel-connected component
                circComp.circCompList.remove(comp)
            # rounding?    
            con[0].value = str(1 / newVal) + 'H'          

# loop through each component, 
# return the list of nodes and the values between them
def getNodes():
    convertParallel()
    clist = []
    for comp in circComp.circCompList:
        clist += [comp.name]

    nodeTups = {}
    nodeDict = {}
    ind = 0
    groundSet = set()
    for comp in circComp.circCompList:
         # for each terminal,
        nodeName = 'n' + str(ind)
        for t in comp.terminals:
            connections = comp.connections[t]
            
            if 'GND' in connections: 
                groundSet.update(connections)
                groundSet.add(t)
                groundSet.discard('GND')
            else: 
                fSet = getSet(t, connections)
                # check if node already exist
                if not (fSet in nodeDict):
                    # add to nodeDict
                    ind += 1
                    nodeName = 'n' + str(ind)
                    nodeDict[fSet] = nodeName
                
                # check if connected to other node
                otherT = getOtherTermSameComp(t)
                node = tInDict(otherT, nodeDict)
                val = getValFromTerminal(t)
                if node != None  and node != nodeName and not nodeInList(node, nodeName, nodeTups):
                    nodeTups[(node, nodeName)] = (val, comp.name)
                elif otherT in groundSet:
                    nodeTups[(nodeName, 'GND')] = (val, comp.name)

    return nodeTups

def getSubsytemDict():
    # dictionary of subsystems
    # values are set of comps in particular subsystem
    subDict = {}
    for comp in circComp.circCompList:
        subSys = comp.subsystem
        # if comp is in a subsystem
        if subSys != '':
            if subSys not in subDict:
                subDict[subSys] = [comp]
            else:
                subDict[subSys].append(comp)
    return subDict

def getSubSystemMap(ssDict, nodeTup):
    ssMap = ssDict.copy()

    for ss in ssDict:
        for comp in ssDict[ss]:
            for tup in nodeTup:
                if nodeTup[tup][1] == comp:
                    ssMap[ss].remove(comp)
                    ssMap[ss].append(tup[0])
                    ssMap[ss].append(tup[1])
                    break
    return ssMap


def getCompNameSS():
    # dictionary of subsystems
    # values are set of comps' names in particular subsystem
    subDict = {}
    for comp in circComp.circCompList:
        subSys = comp.subsystem
        # if comp is in a subsystem
        if subSys != '':
            if subSys not in subDict:
                subDict[subSys] = [comp.name]
            else:
                subDict[subSys].append(comp.name)
    return subDict

def getSubSystemMapName(ssDictN, nodeTup):
    ssMap = ssDictN.copy()
    for ss in ssDictN:
        for comp in ssDictN[ss]:
            for tup in nodeTup:
                if nodeTup[tup][1] == comp:
                    ssMap[ss].remove(comp)
                    ssMap[ss].append(tup[0])
                    ssMap[ss].append(tup[1])
                    break
    return ssMap

def getIndList(nodeTups):
    ind_list = []
    # one dictionary per subsystem
    ind_dict = dict()
    subSysDict = getSubsytemDict()
    # loop through each subsystem
    for subSys in subSysDict:
        for tup in nodeTups:         
            val = nodeTups[tup][0]
            comp = getCompFromName(nodeTups[tup][1])
            compSS = comp.subsystem
            # if has value of inductance and is in current subSys
            if val[-1] == 'H' and subSys == compSS:
                intVal = valToInt(val.split('_')[-1])
                ind_dict[tup] = intVal
        if ind_dict != {}:
            ind_list.append(ind_dict)
        ind_dict = {}
    return ind_list

def getJunctionList(nodeTups):
    junctionList = []
    # one dictionary per subsystem
    junctionDict = dict()
    # loop through each subsystem
    subSysDict = getSubsytemDict()
    for subSys in subSysDict:
        for tup in nodeTups:         
            comp = getCompFromName(nodeTups[tup][1])
            compSS = comp.subsystem
            # if has value of inductance and is in current subSys
            if comp.type == 'junction' and subSys == compSS:
                junctionDict[tup] = comp.name
        if junctionDict != {}:
            junctionList.append(junctionDict)
        junctionDict = {}

    return junctionList

def getCapacitanceGraph(nodeTups):
    capGraph = dict()
    for tup in nodeTups:
        val = nodeTups[tup][0]
        if 'F' in val:
            node1 = tup[0]
            node2 = tup[1]
            capacitance = valToInt(val.split('_')[0])
            if node1 in capGraph:
                capGraph[node1][node2] = capacitance 
            else:
                capGraph[node1] = dict() 
                capGraph[node1][node2] = capacitance 

    return capGraph




def test():
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##                Test Case 1                 ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    #         (S1)       (S1)  
    #       -- C1 --  -- C2 -- 
    #       |                  |
    # (S2)  I2                 I1 (S1)
    #       |                  |
    #        -- C3 -- ---------
    #           (S2)

    C1 = circComp('C1', 'capacitor', ('C1_1', 'C1_2'), '5F', {'C1_1': ['I2_2'], 'C1_2': ['C2_1']}, 'S1')
    C2 = circComp('C2', 'capacitor', ('C2_1', 'C2_2'), '7F', {'C2_1': ['C1_2'], 'C2_2': ['I1_1']}, 'S1') 
    I1 = circComp('I1', 'inductor', ('I1_1', 'I1_2'), '3H', {'I1_1': ['C2_2'], 'I1_2': ['C3_1']}, 'S1') 
    C3 = circComp('C3', 'capacitor', ('C3_1', 'C3_2'), '9F', {'C3_1': ['I1_2'], 'C3_2': ['I2_1']}, 'S2') 
    I2 = circComp('I2', 'inductor', ('I2_1', 'I2_2'), '11H', {'I2_1': ['C3_2'], 'I2_2': ['C1_1']}, 'S2') 
     
    print('Test case 1: nodeTups::')
    nodeT = getNodes()
    print('Node Dictionary::')
    # {('n1', 'n2'): ('5F', 'C1'), ('n2', 'n3'): ('7F', 'C2'), ('n3', 'n4'): ('3H', 'I1'), ('n4', 'n5'): ('9F', 'C3'), ('n1', 'n5'): ('11H', 'I2')}
    print(nodeT)
    print('Subsystem Dictionary::')
    # {'S1': {'I1', 'C1', 'C2'}, 'S2': {'C3', 'I2'}}
    print(getCompNameSS())
    print('Ind_List::')
    # [{('n3', 'n4'): 3}, {('n1', 'n5'): 11}]
    print(getIndList(nodeT))
    print('\n')
    clearCircCompList()

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##                Test Case 2                 ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    #         (S1)       (S1)  
    #        -- C1 -- -- C2 --_ 
    #       |        |         |
    # (S2)  I3       C3 (S1)   I1 (S1)
    #       |        |         |
    #        -- I2 -- -- C4 ---
    #           (S2)     (S2)

    C1 = circComp('C1', 'capacitor', ('C1_1', 'C1_2'), '5F', {'C1_1': ['I3_1'], 'C1_2': ['C2_1', 'C3_1']}, 'S1')
    C2 = circComp('C2', 'capacitor', ('C2_1', 'C2_2'), '7F', {'C2_1': ['C1_2', 'C3_1'], 'C2_2': ['I1_1']}, 'S1') 
    C3 = circComp('C3', 'capacitor', ('C3_1', 'C3_2'), '9F', {'C3_1': ['C1_2', 'C2_1'], 'C3_2': ['C4_1', 'I2_2']}, 'S1') 
    I1 = circComp('I1', 'inductor', ('I1_1', 'I1_2'), '3H', {'I1_1': ['C2_2'], 'I1_2': ['C4_2']}, 'S1') 
    C4 = circComp('C4', 'capacitor', ('C4_1', 'C4_2'), '11F', {'C4_1': ['C3_2', 'I2_2'], 'C4_2': ['I1_2']}, 'S2') 
    I2 = circComp('I2', 'inductor', ('I2_1', 'I2_2'), '20H', {'I2_1': ['I3_2'], 'I2_2': ['C3_2', 'C4_1']}, 'S2') 
    I3 = circComp('I3', 'inductor', ('I3_1', 'I3_2'), '25H', {'I3_1': ['C1_1'], 'I3_2': ['I2_1']}, 'S2') 
     
    print('Test case 2: nodeTups::')
    nodeT = getNodes()
    print('Node Dictionary::')
    # {('n1', 'n2'): ('5F', 'C1'), ('n2', 'n3'): ('7F', 'C2'), ('n2', 'n4'): ('9F', 'C3'), 
    # ('n3', 'n5'): ('3H', 'I1'), ('n4', 'n5'): ('11F', 'C4'), ('n4', 'n6'): ('20H', 'I2'), ('n1', 'n6'): ('25H', 'I3')}
    print(nodeT)
    print('Subsystem Dictionary::')
    # {'S1': {'I1', 'C3', 'C1', 'C2'}, 'S2': {'I3', 'I2', 'C4'}}
    print(getCompNameSS())
    print('Ind_List::')
    # [{('n3', 'n5'): 3}, {('n4', 'n6'): 20, ('n1', 'n6'): 25}]
    print(getIndList(nodeT))
    print('\n')
    clearCircCompList()

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##                MVP Circuit                 ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    

    circComp('J1', 'junction', ('J1_1', 'J1_2'), '2F_10H', 
        {'J1_1': ['GND', 'Cq_1'], 'J1_2': ['Cq_2', 'Cc_1']}, 'transmon_alice')
    circComp('Cq', 'capacitor', ('Cq_1', 'Cq_2'), '5F', 
    {'Cq_1': ['J1_1', 'GND'], 'Cq_2': ['J1_2', 'Cc_1']}, 'transmon_alice') 
    circComp('Cc', 'capacitor', ('Cc_1', 'Cc_2'), '5F', 
        {'Cc_1': ['J1_2', 'Cq_2'], 'Cc_2': ['R1_1', 'Cl_2']}, '') 
    circComp('Cl', 'capacitor', ('Cl_1', 'Cl_2'), '10F', 
        {'Cl_1': ['GND'], 'Cl_2': ['R1_1', 'Cc_2']}, 'readout_resonator') 

    print('MVP circuit: nodeTups::')
    nodeT = getNodes()
    # {('n1', 'GND'): ('7F_10H', 'J1'), ('n1', 'n2'): ('5F', 'Cc'), ('n2', 'GND'): ('10F', 'Cl')}
    print(nodeT)

    print('Capacitance_Graph::')
    # {'n1': {'GND': 7, 'n2': 5}, 'n2': {'GND': 10}}
    print(getCapacitanceGraph(nodeT))

    print('Ind_List::')
    # [{('n1', 'GND'): 10}]
    print(getIndList(nodeT))

    print('Junction_List::')
    # [{('n1', 'GND'): 'J1'}]
    print(getJunctionList(nodeT))

    print('Subsystem Dictionary::')
    # {'transmon_alice': ['J1'], 'readout_resonator': ['Cl']}
    print(getCompNameSS())

    ssDict = getCompNameSS()
    print('Subsystem Map::')
    # {'transmon_alice': ['n1', 'GND'], 'readout_resonator': ['n2', 'GND']}
    print(getSubSystemMapName(ssDict, nodeT))


    print('\n')
    clearCircCompList()



test()
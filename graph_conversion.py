# Quantum SPICE 
# Converts circuit information to capacitance & inductance graph

# arbitrary class for each components in the quantum circuit
class CircuitComponent(object):

    def __init__(self, name, label, terminals, value, connections, subsystem=None):
        # name (string) -> e.g. C1, I2
        self._name = name
        # label (string) => e.g. capacitor, inductor
        self._label = label
        # terminal (string tuple) => e.g. (C1_1, C1_2)
        self._terminals = terminals
        # value (string) => e.g. 4F, 15H
        self._value = value
        # connection (dictionary w string key and string list value) 
        # e.g. {C1_1: [C2_1, I1_2], C1_2: []}
        # stores list of connections between 
        # self.terminals (key) & other terminals (values)
        # no connection is shown by []
        self._connections = connections
        self._subsystem = subsystem   
    
    @property
    def name(self):
        return self._name 
    
    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def label(self):
        return self._label 
    
    @label.setter
    def label(self, new_label):
        self._label = new_label

    @property
    def terminals(self):
        return self._terminals
    
    @terminals.setter
    def terminals(self, new_terminals):
        self._terminals = new_terminals

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value):
        self._value = new_value
    
    @property 
    def connections(self):
        return self._connections 

    @connections.setter 
    def connections(self, new_connections):
        self._connections = new_connections

    @property 
    def subsystem(self):
        return self._subsystem

    @subsystem.setter 
    def subsystem(self, new_subsystem):
        self._subsystem = new_subsystem

    def __del__(self):
        self._name = None
        self._label = None
        self._terminals = None
        self._value = None
        self._connections = None
        self._subsystem = None
        del self 

class Subsystem(object):

    subSystemMap = []

    def __init__(self, name, sys_label, options, nodes):
        self._name = name
        self._sys_label = sys_label 
        self._options = options
        self._components = []
        self._nodes = nodes
        # add circComp instance to circCompList
        Subsystem.subSystemMap.append(self)  

class Circuit(object):
    def __init__(self, circuit_component_list):
        """
        Create a circuit object to manage circuit-level operations using a circuit component list and
        circuit-level methods
        """
        self._circuit_component_list = circuit_component_list

    def clear_circuit_component_list(self):
        """
        Clear the circuit component list
        """
        for comp in self._circuit_component_list:
            CircuitComponent.__del__(comp)
        self._circuit_component_list = []

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##              Helper Functions              ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    # return the circComp that has the input terminal
    def get_component_from_terminal(self, terminal):
        """
        Return the CircuitComponent that has the give input terminal
        """
        for component in self._circuit_component_list:
            if terminal in component.terminals:
                return component
        raise Exception("Terminal " + terminal + " doesn't exist, perhaps you have a wrong test case?")


    # return other terminal in the same component 
    # (assume only two terminals in a single componenet)
    def get_other_terminal_same_component(self, terminal):
        component = self.get_component_from_terminal(terminal)
        for t in component.terminals:
            if (t != terminal):
                return t
        
    # return the value of the comp that 
    # the terminal is in
    def get_value_from_terminal(self, terminal):
        component = self.get_component_from_terminal(terminal)
        return component.value

    def get_component_from_name(self, name):
        for comp in self._circuit_component_list:
            if comp.name == name:
                return comp
        raise Exception(comp + " comp doesn't exist")  

    def get_set(self, term, cons):
        conSet = set()
        conSet.update(cons)
        conSet.add(term)
        conSet.discard('GND')
        # nodeDict's key is frozenset
        return frozenset(conSet)

    # return node name if terminal is in nodeDict
    # otherwise, return None
    def check_terminal_in_dict(self, term, dict):
        for entry in dict:
            if term in entry:
                return dict[entry]
        return None

    def node_in_list(self, node1, node2, nTups):
        if (node1, node2) in nTups or (node2, node1) in nTups:
            return True
        else: 
            return False

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##              Main Functions              ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    def convert_parallel(self):
        # make 2d list of comps connected in parallel
        parallelConnections = []
        existingComp = []
        for comp in self._circuit_component_list:
            if comp not in existingComp:
                conInParallel = [comp]
                connected1 = []
                for term in comp.connections:
                    for con in comp.connections[term]:
                        # skip resonator and ground node 
                        if con[0] != 'R' and con != 'GND':
                            conComp = self.get_component_from_terminal(con)
                            # if same label, add in the same list 
                            if (comp.label == 'junction') or (conComp.label == comp.label) or (conComp.label == 'junction'):
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
                if (comp.label == 'junction'):
                    hasJunction = True
                    junction = comp

            # if there's a junction, add capacitance and inductance
            # of other parallel-connected components to the junction
            if hasJunction: 
                newCap = junction.value['capacitance']
                newInd = junction.value['inductance']
                for comp in con:
                    if (comp.name != junction.name):
                        # add capacitance and inductance in parallel
                        if comp.label == 'junction':
                            cap = comp.value['capacitance']
                            indu = comp.value['inductance']
                            newCap += cap
                            newInd +=  1 / indu
                        elif comp.label == 'capacitor':
                            newCap += comp.value['capacitance']
                        elif comp.label == 'inductor':
                            newInd += 1 / comp.value['inductance']

                        # remove redundant connections
                        for t in comp.terminals:
                            for origT in junction.terminals:
                                if t in junction.connections[origT]:
                                    junction.connections[origT].remove(t) 

                        # remove terminals of comp in all other comps' connections
                        for itComp in self._circuit_component_list: 
                            for itT in itComp.terminals:
                                for compT in comp.terminals:
                                    if compT in itComp.connections[itT]:
                                        itComp.connections[itT].remove(compT)

                        # remove parallel-connected component
                        self._circuit_component_list.remove(comp)    

                # update capacitance and inductance of the junction  
                junction.value = {'capacitance': newCap, 'inductance': newInd}
            # if there're only capacitors
            elif con[0].label == 'capacitor':       
                for comp in con[1:]:
                    # add capacitance in parallel
                    newVal += comp.value['capacitance']
                    # remove redundant connections
                    for t in comp.terminals:
                        for origT in con[0].terminals:
                            if t in con[0].connections[origT]:
                                con[0].connections[origT].remove(t) 
                    # remove parallel-connected component
                    self._circuit_component_list.remove(comp)      
                con[0].value = str(newVal) + 'F'          
            # if there're only inductors
            elif con[0].label == 'inductor':
                for comp in con[1:]:
                    # inverse -- 
                    newVal +=  1 / comp.value['inductance']
                    # remove redundant connections
                    for t in comp.terminals:
                        for origT in con[0].terminals:
                            if t in con[0].connections[origT]:
                                con[0].connections[origT].remove(t)  
                    # remove parallel-connected component
                    self._circuit_component_list.remove(comp)
                # rounding?    
                con[0].value = str(1 / newVal) + 'H'          

    # loop through each component, 
    # return the list of nodes and the values between them
    def get_nodes(self):
        self.convert_parallel()
        clist = []
        for comp in self._circuit_component_list:
            clist += [comp.name]

        nodeTups = {}
        nodeDict = {}
        ind = 0
        groundSet = set()
        for comp in self._circuit_component_list:
            # for each terminal,
            nodeName = 'n' + str(ind)
            for t in comp.terminals:
                connections = comp.connections[t]
                
                if 'GND' in connections: 
                    groundSet.update(connections)
                    groundSet.add(t)
                    groundSet.discard('GND')
                else: 
                    fSet = self.get_set(t, connections)
                    # check if node already exist
                    if not (fSet in nodeDict):
                        # add to nodeDict
                        ind += 1
                        nodeName = 'n' + str(ind)
                        nodeDict[fSet] = nodeName
                    
                    # check if connected to other node
                    otherT = self.get_other_terminal_same_component(t)
                    node = self.check_terminal_in_dict(otherT, nodeDict)
                    val = self.get_value_from_terminal(t)
                    if ((node != None) and (node != nodeName) 
                        and (not self.node_in_list(node, nodeName, nodeTups))):
                        nodeTups[(node, nodeName)] = (val, comp.name)
                    elif otherT in groundSet:
                        nodeTups[(nodeName, 'GND')] = (val, comp.name)

        return nodeTups

    def get_component_name_subsystem(self):
        # dictionary of subsystems
        # values are set of comps' names in particular subsystem
        subDict = {}
        for comp in self._circuit_component_list:
            subSys = comp.subsystem
            # if comp is in a subsystem
            if subSys != '':
                if subSys not in subDict:
                    subDict[subSys] = [comp.name]
                else:
                    subDict[subSys].append(comp.name)
        return subDict

    # convert componenets in subsystem map as nodes
    def get_subsystem_map(self, subsystemDict, nodeTup):
        subsystemMap = subsystemDict.copy()
        # loop through all subsystems
        for subsystem in subsystemDict:
            # for each component in a subsystem
            for comp in subsystemDict[subsystem]:
                for tup in nodeTup:
                    if nodeTup[tup][1] == comp:
                        subsystemMap[subsystem].remove(comp)
                        # convert component to nodes it's connected to
                        if tup[0] not in subsystemMap[subsystem]:
                            subsystemMap[subsystem].append(tup[0])
                        if tup[1] not in subsystemMap[subsystem]:
                            subsystemMap[subsystem].append(tup[1])
                        break
        return subsystemMap

    def get_inductor_list(self, nodeTups):
        ind_list = []
        # one dictionary per subsystem
        ind_dict = dict()
        subSysDict = self.get_component_name_subsystem()
        # loop through each subsystem
        for subSys in subSysDict:
            for tup in nodeTups:         
                val = nodeTups[tup][0]
                comp = self.get_component_from_name(nodeTups[tup][1])
                compSS = comp.subsystem
                inductance = val['inductance']
                # if has value of inductance and is in current subSys
                if subSys == compSS and inductance > 0:
                    ind_dict[tup] = inductance
            if ind_dict != {}:
                ind_list.append(ind_dict)
            ind_dict = {}
        return ind_list

    def get_junction_list(self, nodeTups):
        junctionList = []
        # one dictionary per subsystem
        junctionDict = dict()
        # loop through each subsystem
        subSysDict = self.get_component_name_subsystem()
        for subSys in subSysDict:
            for tup in nodeTups:         
                comp = self.get_component_from_name(nodeTups[tup][1])
                compSS = comp.subsystem
                # if has value of inductance and is in current subSys
                if comp.label == 'junction' and subSys == compSS:
                    junctionDict[tup] = comp.name
            if junctionDict != {}:
                junctionList.append(junctionDict)
            junctionDict = {}

        return junctionList

    def get_capacitance_graph(self, nodeTups):
        capGraph = dict()
        for tup in nodeTups:
            val = nodeTups[tup][0]
            if val['capacitance'] > 0:
                node1 = tup[0]
                node2 = tup[1]
                capacitance = val['capacitance']
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

    C1 = CircuitComponent('C1', 'capacitor', ('C1_1', 'C1_2'), 
    {'capacitance': 5, 'inductance': 0}, {'C1_1': ['I2_2'], 'C1_2': ['C2_1']}, 'S1')
    C2 = CircuitComponent('C2', 'capacitor', ('C2_1', 'C2_2'), 
    {'capacitance': 7, 'inductance': 0}, {'C2_1': ['C1_2'], 'C2_2': ['I1_1']}, 'S1') 
    I1 = CircuitComponent('I1', 'inductor', ('I1_1', 'I1_2'), 
    {'capacitance': 0, 'inductance': 3}, {'I1_1': ['C2_2'], 'I1_2': ['C3_1']}, 'S1') 
    C3 = CircuitComponent('C3', 'capacitor', ('C3_1', 'C3_2'), 
    {'capacitance': 9, 'inductance': 0}, {'C3_1': ['I1_2'], 'C3_2': ['I2_1']}, 'S2') 
    I2 = CircuitComponent('I2', 'inductor', ('I2_1', 'I2_2'), 
    {'capacitance': 0, 'inductance': 11}, {'I2_1': ['C3_2'], 'I2_2': ['C1_1']}, 'S2') 
     
    circuit1 = Circuit([C1, C2, I1, C3, I2])

    print('Test case 1: nodeTups::')
    nodeT = circuit1.get_nodes()
    print('Node Dictionary::')
    # {('n1', 'n2'): ('5F', 'C1'), ('n2', 'n3'): ('7F', 'C2'), ('n3', 'n4'): ('3H', 'I1'), ('n4', 'n5'): ('9F', 'C3'), ('n1', 'n5'): ('11H', 'I2')}
    print(nodeT)
    print('Subsystem Dictionary::')
    # {'S1': {'I1', 'C1', 'C2'}, 'S2': {'C3', 'I2'}}
    print(circuit1.get_component_name_subsystem())
    print('Ind_List::')
    # [{('n3', 'n4'): 3}, {('n1', 'n5'): 11}]
    print(circuit1.get_inductor_list(nodeT))
    print('\n')

    circuit1.clear_circuit_component_list()

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

    C1 = CircuitComponent('C1', 'capacitor', ('C1_1', 'C1_2'), 
    {'capacitance': 5, 'inductance': 0}, {'C1_1': ['I3_1'], 'C1_2': ['C2_1', 'C3_1']}, 'S1')
    C2 = CircuitComponent('C2', 'capacitor', ('C2_1', 'C2_2'), 
    {'capacitance': 7, 'inductance': 0}, {'C2_1': ['C1_2', 'C3_1'], 'C2_2': ['I1_1']}, 'S1') 
    C3 = CircuitComponent('C3', 'capacitor', ('C3_1', 'C3_2'), 
    {'capacitance': 9, 'inductance': 0}, {'C3_1': ['C1_2', 'C2_1'], 'C3_2': ['C4_1', 'I2_2']}, 'S1') 
    I1 = CircuitComponent('I1', 'inductor', ('I1_1', 'I1_2'), 
    {'capacitance': 0, 'inductance': 3}, {'I1_1': ['C2_2'], 'I1_2': ['C4_2']}, 'S1') 
    C4 = CircuitComponent('C4', 'capacitor', ('C4_1', 'C4_2'),
    {'capacitance': 11, 'inductance': 0}, {'C4_1': ['C3_2', 'I2_2'], 'C4_2': ['I1_2']}, 'S2') 
    I2 = CircuitComponent('I2', 'inductor', ('I2_1', 'I2_2'), 
    {'capacitance': 0, 'inductance': 20}, {'I2_1': ['I3_2'], 'I2_2': ['C3_2', 'C4_1']}, 'S2') 
    I3 = CircuitComponent('I3', 'inductor', ('I3_1', 'I3_2'), 
    {'capacitance': 0, 'inductance': 25}, {'I3_1': ['C1_1'], 'I3_2': ['I2_1']}, 'S2') 
    
    circuit2 = Circuit([C1, C2, C3, I1, C4, I2, I3])

    print('Test case 2: nodeTups::')
    nodeT = circuit2.get_nodes()
    print('Node Dictionary::')
    # {('n1', 'n2'): ('5F', 'C1'), ('n2', 'n3'): ('7F', 'C2'), ('n2', 'n4'): ('9F', 'C3'), 
    # ('n3', 'n5'): ('3H', 'I1'), ('n4', 'n5'): ('11F', 'C4'), ('n4', 'n6'): ('20H', 'I2'), ('n1', 'n6'): ('25H', 'I3')}
    print(nodeT)
    print('Subsystem Dictionary::')
    # {'S1': {'I1', 'C3', 'C1', 'C2'}, 'S2': {'I3', 'I2', 'C4'}}
    print(circuit2.get_component_name_subsystem())
    print('Ind_List::')
    # [{('n3', 'n5'): 3}, {('n4', 'n6'): 20, ('n1', 'n6'): 25}]
    print(circuit2.get_inductor_list(nodeT))
    print('\n')
    circuit2.clear_circuit_component_list()

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    ##                MVP Circuit                 ##
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    

    J1 = CircuitComponent('J1', 'junction', ('J1_1', 'J1_2'), 
    {'capacitance': 2, 'inductance': 10}, {'J1_1': ['GND', 'Cq_1'], 'J1_2': ['Cq_2', 'Cc_1']}, 
    'transmon_alice')

    Cq = CircuitComponent('Cq', 'capacitor', ('Cq_1', 'Cq_2'), 
    {'capacitance': 5, 'inductance': 0}, {'Cq_1': ['J1_1', 'GND'], 'Cq_2': ['J1_2', 'Cc_1']}, 
    'transmon_alice') 
    Cc = CircuitComponent('Cc', 'capacitor', ('Cc_1', 'Cc_2'), 
    {'capacitance': 5, 'inductance': 0}, {'Cc_1': ['J1_2', 'Cq_2'], 'Cc_2': ['R1_1', 'Cl_2']}, 
    '') 
    Cl = CircuitComponent('Cl', 'capacitor', ('Cl_1', 'Cl_2'), 
    {'capacitance': 10, 'inductance': 0}, {'Cl_1': ['GND'], 'Cl_2': ['R1_1', 'Cc_2']}, 
    'readout_resonator') 
    
    circuit_mvp = Circuit([J1, Cq, Cc, Cl])

    transmon_alice = Subsystem(name='transmon_alice', sys_label='TRANSMON', 
        options=None, nodes=['j1'])

    print('MVP circuit: nodeTups::')
    nodeT = circuit_mvp.get_nodes()
    # {('n1', 'GND'): ('7F_10H', 'J1'), ('n1', 'n2'): ('5F', 'Cc'), ('n2', 'GND'): ('10F', 'Cl')}
    print(nodeT)

    print('Capacitance_Graph::')
    # {'n1': {'GND': 7, 'n2': 5}, 'n2': {'GND': 10}}
    print(circuit_mvp.get_capacitance_graph(nodeT))

    print('Ind_List::')
    # [{('n1', 'GND'): 10}]
    print(circuit_mvp.get_inductor_list(nodeT))

    print('Junction_List::')
    # [{('n1', 'GND'): 'J1'}]
    print(circuit_mvp.get_junction_list(nodeT))

    print('Subsystem Dictionary::')
    # {'transmon_alice': ['J1'], 'readout_resonator': ['Cl']}
    print(circuit_mvp.get_component_name_subsystem())

    ssDict = circuit_mvp.get_component_name_subsystem()
    print('Subsystem Map::')
    # {'transmon_alice': ['n1', 'GND'], 'readout_resonator': ['n2', 'GND']}
    print(circuit_mvp.get_subsystem_map(ssDict, nodeT))


    print('\n')
    circuit_mvp.clear_circuit_component_list()



test()
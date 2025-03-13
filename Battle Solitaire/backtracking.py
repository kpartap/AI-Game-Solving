from csp import Constraint, Variable, CSP
from constraints import *
import random

class UnassignedVars:
    '''class for holding the unassigned variables of a CSP. We can extract
       from, re-initialize it, and return variables to it.  Object is
       initialized by passing a select_criteria (to determine the
       order variables are extracted) and the CSP object.

       select_criteria = ['random', 'fixed', 'mrv'] with
       'random' == select a random unassigned variable
       'fixed'  == follow the ordering of the CSP variables (i.e.,
                   csp.variables()[0] before csp.variables()[1]
       'mrv'    == select the variable with minimum values in its current domain
                   break ties by the ordering in the CSP variables.
    '''
    def __init__(self, select_criteria, csp):
        if select_criteria not in ['random', 'fixed', 'mrv']:
            pass #print "Error UnassignedVars given an illegal selection criteria {}. Must be one of 'random', 'stack', 'queue', or 'mrv'".format(select_criteria)
        self.unassigned = list(csp.variables())
        self.csp = csp
        self._select = select_criteria
        if select_criteria == 'fixed':
            #reverse unassigned list so that we can add and extract from the back
            self.unassigned.reverse()

    def extract(self):
        if not self.unassigned:
            pass #print "Warning, extracting from empty unassigned list"
            return None
        if self._select == 'random':
            i = random.randint(0,len(self.unassigned)-1)
            nxtvar = self.unassigned[i]
            self.unassigned[i] = self.unassigned[-1]
            self.unassigned.pop()
            return nxtvar
        if self._select == 'fixed':
            return self.unassigned.pop()
        if self._select == 'mrv':
            nxtvar = min(self.unassigned, key=lambda v: v.curDomainSize())
            self.unassigned.remove(nxtvar)
            return nxtvar

    def empty(self):
        return len(self.unassigned) == 0

    def insert(self, var):
        if not var in self.csp.variables():
            pass #print "Error, trying to insert variable {} in unassigned that is not in the CSP problem".format(var.name())
        else:
            self.unassigned.append(var)

def bt_search(algo, csp, variableHeuristic, allSolutions, trace, size, ship_cons, board, specified):
    '''Main interface routine for calling different forms of backtracking search
       algorithm is one of ['BT', 'FC', 'GAC']
       csp is a CSP object specifying the csp problem to solve
       variableHeuristic is one of ['random', 'fixed', 'mrv']
       allSolutions True or False. True means we want to find all solutions.
       trace True of False. True means turn on tracing of the algorithm

       bt_search returns a list of solutions. Each solution is itself a list
       of pairs (var, value). Where var is a Variable object, and value is
       a value from its domain.
    '''
    varHeuristics = ['random', 'fixed', 'mrv']
    algorithms = ['BT', 'GAC']

    #statistics
    bt_search.nodesExplored = 0

    if variableHeuristic not in varHeuristics:
        pass #print "Error. Unknown variable heursitics {}. Must be one of {}.".format(
            #variableHeuristic, varHeuristics)
    if algo not in algorithms:
        pass #print "Error. Unknown algorithm heursitics {}. Must be one of {}.".format(
            #algo, algorithms)

    uv = UnassignedVars(variableHeuristic,csp)
    Variable.clearUndoDict()
    for v in csp.variables():
        v.reset()
    if algo == 'BT':
         solutions = BT(uv, csp, allSolutions, trace)
    elif algo == 'GAC':
        GacEnforce(csp.constraints(), csp, None, None) #GAC at the root
        solutions = GAC(uv, csp, board, size, ship_cons, specified)

    return solutions, bt_search.nodesExplored

def BT(unAssignedVars, csp, allSolutions, trace):
    '''Backtracking Search. unAssignedVars is the current set of
       unassigned variables.  csp is the csp problem, allSolutions is
       True if you want all solutionss trace if you want some tracing
       of variable assignments tried and constraints failed. Returns
       the set of solutions found.

      To handle finding 'allSolutions', at every stage we collect
      up the solutions returned by the recursive  calls, and
      then return a list of all of them.

      If we are only looking for one solution we stop trying
      further values of the variable currently being tried as
      soon as one of the recursive calls returns some solutions.
    '''
    if unAssignedVars.empty():
        if trace: pass #print "{} Solution Found".format(csp.name())
        soln = []
        for v in csp.variables():
            soln.append((v, v.getValue()))
        return [soln]  #each call returns a list of solutions found
    bt_search.nodesExplored += 1
    solns = []         #so far we have no solutions recursive calls
    nxtvar = unAssignedVars.extract()
    if trace: pass #print "==>Trying {}".format(nxtvar.name())
    for val in nxtvar.domain():
        if trace: pass #print "==> {} = {}".format(nxtvar.name(), val)
        nxtvar.setValue(val)
        constraintsOK = True
        for cnstr in csp.constraintsOf(nxtvar):
            if cnstr.numUnassigned() == 0:
                if not cnstr.check():
                    constraintsOK = False
                    if trace: pass #print "<==falsified constraint\n"
                    break
        if constraintsOK:
            new_solns = BT(unAssignedVars, csp, allSolutions, trace)
            if new_solns:
                solns.extend(new_solns)
            if len(solns) > 0 and not allSolutions:
                break  #don't bother with other values of nxtvar
                       #as we found a soln.
    nxtvar.unAssign()
    unAssignedVars.insert(nxtvar)
    return solns


def GacEnforce(cons, csp, var_assign, val_assign):
    cons = csp.constraints()
    while len(cons) != 0:
        cnstr = cons.pop()
        for var in cnstr.scope():
            for val in var.curDomain():
                if not cnstr.hasSupport(var,val):
                    var.pruneValue(val,var_assign, val_assign)
                    if var.curDomainSize() == 0:
                        return "DWO"
                    for recheck in csp.constraintsOf(var):
                        if recheck != cnstr and recheck not in cons:
                            cons.append(recheck)
    return "OK"


def GAC(unAssignedVars,csp, board, size, ship_cons, specified):
    if unAssignedVars.empty():
        soln = []
        for var in csp.variables():
            if int(var._name) > 0:
                soln.append((var,var.getValue()))
        return [soln]
    bt_search.nodesExplored += 1
    solns = []
    next_var = unAssignedVars.extract()
    for val in next_var.curDomain():
        next_var.setValue(val)
        noDWO = True
        if GacEnforce(csp.constraintsOf(next_var), csp, next_var, val) == "DWO":
            noDWO = False
        if noDWO and not check_pruned(csp, ship_cons, size) and not check_placement(csp, size, specified):
            new_solns = GAC(unAssignedVars, csp, board, size, ship_cons, specified)
            if new_solns:
                carr, battle, cruise, dest, sub, var_dict = count_ships(new_solns[0], size)
                if sub == int(ship_cons[0]) and dest == int(ship_cons[1]) and cruise == int(ship_cons[2]) and battle == int(ship_cons[3]) and carr == int(ship_cons[4]):
                    match = board_check(board, var_dict, size)
                    if (match):
                        solns.extend(new_solns)
                        if len(solns) > 0:
                            break
        next_var.restoreValues(next_var,val)
    next_var.unAssign()
    unAssignedVars.insert(next_var)
    return solns


def check_pruned(csp, ship_cons, size):
    solutions = []
    for var in csp.variables():
        if int(var._name) > 0:
            solutions.append((var,var.getValue()))
    
    num_carr, num_battle, num_cruise, num_dest, num_sub, new_var_dict = ship_number_check(solutions, size)
    if num_sub > int(ship_cons[0]) or num_dest > int(ship_cons[1]) or  num_cruise > int(ship_cons[2]) or num_battle > int(ship_cons[3]) or num_carr > int(ship_cons[4]):
        return True
    return False

def ship_number_check(solution, size):
    num_carr = 0
    num_battle = 0
    num_cruise = 0
    num_dest = 0
    num_sub = 0
    var_dict = {}
    for (var, val) in solution:
        var_dict[int(var.name())] = val
    for i in range(1, size-1):
        for j in range(1, size-1):
            down = None
            up = None
            right = None
            left = None
            if (i < (size - 5) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S" and var_dict[((i+3)*size+j)] == "S" and var_dict[((i+4)*size+j)] == "S"):
                num_carr += 1
            elif (i < (size - 4) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S" and var_dict[((i+3)*size+j)] == "S"):
                if i != size - 5:
                    down = var_dict[((i+4)*size+j)]
                if i != 1:
                    up = var_dict[((i-1)*size+j)]
                if down == "." and up == ".":
                    num_battle += 1
            elif (i < (size - 3) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S"):
                if i != size - 4:
                    down = var_dict[((i+3)*size+j)]
                if i != 1:
                    up = var_dict[((i-1)*size+j)]
                if down == "." and up == ".":
                    num_cruise += 1
            elif (i < (size - 2) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S"):
                if i != size - 3:
                    down = var_dict[((i+2)*size+j)]
                if i != 1:
                    up = var_dict[((i-1)*size+j)]
                if down == "." and up == ".":
                    num_dest += 1
            if (j < (size - 5) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S" and var_dict[(i*size+j+3)] == "S" and  var_dict[(i*size+j+4)] == "S"):
                num_carr += 1
            if (j < (size - 4) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S" and var_dict[(i*size+j+3)] == "S"):
                if j != size - 5:
                    right = var_dict[(i*size+j+4)] 
                if j != 1:
                    left = var_dict[(i*size+j-1)]
                if right == "." and left == ".":
                    num_battle += 1
            elif (j < (size - 3) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S"):
                if j != size - 4:
                    right = var_dict[(i*size+j+3)] 
                if j != 1:
                    left = var_dict[(i*size+j-1)]
                if right == "." and left == ".":
                    num_cruise += 1
            elif (j < (size - 2) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S"):
                if j != size - 3:
                    right = var_dict[(i*size+j+2)] 
                if j != 1:
                    left = var_dict[(i*size+j-1)]
                if right == "." and left == ".":
                    num_dest += 1
            
    down = None
    up = None
    right = None
    left = None
    for i in range(1, size-1):
        for j in range(1, size-1):
            single = False
            if var_dict[(i*size+j)] == "S":
                if i == 1 and j == 1:
                    right = var_dict[((i)*size+j+1)]
                    down = var_dict[((i+1)*size+j)]
                    if down == "." and right == ".":
                        single = True
                elif i == 1 and j == size-2:
                    left = var_dict[((i)*size+j-1)]
                    down = var_dict[((i+1)*size+j)]
                    if down == "." and left == ".":
                        single = True
                elif i == size - 2 and j == 1:
                    up = var_dict[((i-1)*size+j)]
                    right = var_dict[((i)*size+j+1)]
                    if up == "." and right == ".":
                        single = True
                elif i == size - 2 and j == size - 2:
                    up = var_dict[((i-1)*size+j)]
                    left = var_dict[((i)*size+j-1)]
                    if up == "." and left == ".":
                        single = True
                elif i == 1:
                    down = var_dict[((i+1)*size+j)]
                    left = var_dict[((i)*size+j-1)]
                    right = var_dict[((i)*size+j+1)]
                    if down == "." and left == "." and right == ".":
                        single = True
                elif j == 1:
                    up = var_dict[((i-1)*size+j)]
                    down = var_dict[((i+1)*size+j)]
                    right = var_dict[((i)*size+j+1)]
                    if up == "." and down == "." and right == ".":
                        single = True
                elif i == size - 2:
                    up = var_dict[((i-1)*size+j)]
                    left = var_dict[((i)*size+j-1)]
                    right = var_dict[((i)*size+j+1)]
                    if up == "." and left == "." and right == ".":
                        single = True
                elif j == size - 2:
                    up = var_dict[((i-1)*size+j)]
                    left = var_dict[((i)*size+j-1)]
                    down = var_dict[((i+1)*size+j)]
                    if up == "." and left == "." and down == ".":
                        single = True
                else:
                    up = var_dict[((i-1)*size+j)]
                    left = var_dict[((i)*size+j-1)]
                    down = var_dict[((i+1)*size+j)]
                    right = var_dict[((i)*size+j+1)]
                    if up == "." and left == "." and down == "." and right == ".":
                        single = True
                if single:
                    num_sub += 1
    
    return num_carr, num_battle, num_cruise, num_dest, num_sub, var_dict


def check_placement(csp, size, specified):
    soln_m = []
    for var in csp.variables():
        if int(var._name) > 0:
            soln_m.append((var,var.getValue()))

    var_dict = {}
    for (var, val) in soln_m:
        var_dict[int(var.name())] = val

    for (i, j, coord) in specified:
        if coord == "M":
            if j == 1 and var_dict[int(i*size+j+1)] == "S":
                return True
            elif i == 1 and var_dict[int((i+1)*size+j)] == "S":
                return True
            elif j == size - 2 and var_dict[int(i*size+j-1)] == "S":
                return True
            elif i == size - 2 and var_dict[int((i-1)*size+j)] == "S":
                return True
        elif coord == "<" and var_dict[int(i*size+j-1)] == "S":
            return True
        elif coord == ">" and var_dict[int(i*size+j+1)] == "S":
            return True
        elif coord == "^" and var_dict[int((i-1)*size+j)] == "S":
            return True
        elif coord == "v" and var_dict[int((i+1)*size+j)] == "S":
            return True
    return False


def board_check(originalB, var_dict, size):
    for i in range(1, size-1):
        for j in range(1, size-1):
            sol_val = var_dict[(i*size+j)]
            orig_val = originalB[i][j]
            if orig_val!= "0" and sol_val != orig_val:
                return False
    return True

def count_ships(solution, size):
    num_carr = 0
    num_battle = 0
    num_cruise = 0
    num_dest = 0
    num_sub = 0
    var_dict = {}
    for (var, val) in solution:
        var_dict[int(var.name())] = val
    for i in range(1, size-1):
        for j in range(1, size-1):
            if (i < (size - 5) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S" and var_dict[((i+3)*size+j)] == "S" and var_dict[((i+4)*size+j)] == "S"):
                num_carr += 1
                var_dict[((i)*size+j)] = "^"
                var_dict[((i+1)*size+j)] = "M"
                var_dict[((i+2)*size+j)] = "M"
                var_dict[((i+3)*size+j)] = "M"
                var_dict[((i+4)*size+j)] = "v"
            elif (i < (size - 4) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S" and var_dict[((i+3)*size+j)] == "S"):
                num_battle += 1
                var_dict[((i)*size+j)] = "^"
                var_dict[((i+1)*size+j)] = "M"
                var_dict[((i+2)*size+j)] = "M"
                var_dict[((i+3)*size+j)] = "v"
            elif (i < (size - 3) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S" and var_dict[((i+2)*size+j)] == "S"):
                num_cruise += 1
                var_dict[((i)*size+j)] = "^"
                var_dict[((i+1)*size+j)]= "M"
                var_dict[((i+2)*size+j)] = "v"
            elif (i < (size - 2) and var_dict[(i*size+j)] == "S" and var_dict[((i+1)*size+j)] == "S"):
                num_dest += 1
                var_dict[((i)*size+j)] = "^"
                var_dict[((i+1)*size+j)] = "v"
            if (j < (size - 5) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S" and var_dict[(i*size+j+3)] == "S" and var_dict[(i*size+j+4)] == "S"):
                num_carr += 1
                var_dict[(i*size+j)] = "<"
                var_dict[(i*size+j+1 )] ="M"
                var_dict[(i*size+j+2 )] ="M"
                var_dict[(i*size+j+3 )] ="M"
                var_dict[(i*size+j+4 )] =">"
            elif (j < (size - 4) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S" and var_dict[(i*size+j+3)] == "S"):
                num_battle += 1
                var_dict[(i*size+j)] = "<"
                var_dict[(i*size+j+1 )] ="M"
                var_dict[(i*size+j+2 )] ="M"
                var_dict[(i*size+j+3 )] =">"
            elif (j < (size - 3) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S" and var_dict[(i*size+j+2)] == "S"):
                num_cruise += 1
                var_dict[(i*size+j)] = "<"
                var_dict[(i*size+j+1)] = "M"
                var_dict[(i*size+j+2)] = ">"
            elif (j < (size - 2) and var_dict[(i*size+j)] == "S" and var_dict[(i*size+j+1)] == "S"):
                num_dest += 1
                var_dict[(i*size+j)] = "<"
                var_dict[(i*size+j+1)] = ">"
            
    for i in range(1, size-1):
        for j in range(1, size-1):
            if var_dict[(i*size+j)] == "S":
                num_sub += 1
    return num_carr, num_battle, num_cruise, num_dest, num_sub, var_dict
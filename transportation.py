# Written by: Areesh Mittal; Sept 2018

# This file describes the Pyomo model for the transportation prolem

import pyomo.environ as pe

capacities = [2, 3, 3]

demands = [4, 4]

costs = [[1, 2],
         [2, 2],
         [2, 3]]

nF = len(capacities) # number of factories
nW = len(demands)    # number of warehouses

# Create the model
model = pe.ConcreteModel()

# Tell pyomo to read in dual-variable information from the solver;
# Of course, duals can only be obtained for LPs, not MIPs
model.dual = pe.Suffix(direction = pe.Suffix.IMPORT)

# ------ SETS ---------

model.facilities  = pe.Set(initialize = range(nF))
model.warehouses  = pe.Set(initialize = range(nW))
# Sets can be initialized from any iterable object, eg, list, scipy array,
# pandas dataframe column, dictionary keys, etc

# To view the set elements:
model.facilities.pprint()

# ------PARAMETERS--------

# Parameters are initialized from a function.
# The initialization function ALWAYS takes model as the first argument, 
# and then one argument for each index in order

def cost_func(model,f,w): 
    return costs[f][w]
model.cost = pe.Param(model.facilities, model.warehouses, initialize = cost_func)

# In the Param function, list all index sets first, then initialization function

# Let's view what we created
model.cost.pprint()

model.capacity = pe.Param(model.facilities, initialize = lambda model,f: capacities[f])
model.demand = pe.Param(model.warehouses,   initialize = lambda model,w: demands[w])


# -------------VARIABLES------------

model.X = pe.Var(model.facilities, model.warehouses, domain = pe.NonNegativeReals)
# List all index sets first, and then the domain
# Other options for domain: pe.Reals, pe.NonPositiveReals, pe.Binary,
#                   pe.Integers, pe.NonNegativeIntegers, pe.NonPositiveIntegers


# ------CONSTRAINTS-----------

#Constraints are defined through "rules".
#Each rule is a function. It ALWAYS takes model as the firt argument. Then an
#argument for each index over which the constraint is defined

def capacity_rule(model, f):
    return (sum(model.X[f,w] for w in model.warehouses) <= model.capacity[f])
    
model.CapacityCons = pe.Constraint(model.facilities, rule = capacity_rule)

# Use >= for "greater than or equal to" and == for "equals to" constraints

# lambda functions can also be used to define constraint rules

# You may want to print the constraints to see if you have coded them correctly:
model.CapacityCons.pprint()

def demand_rule(model, w):
    return (sum(model.X[f,w] for f in model.facilities) >= model.demand[w])  
model.DemandCons = pe.Constraint(model.warehouses, rule = demand_rule)

# If you want to deactivate/activate constraints:
#model.CapacityCons.deactivate()
#model.CapacityCons.activate()


# ------OBJECTIVE-----------

def obj_rule(model):
    return sum(model.cost[f,w] * model.X[f,w] for f in model.facilities for w in model.warehouses)
    # Same as:
    #return pe.summation(model.cost, model.X)
    # Use 'pe.summation' only when summing over all indices; all inputs should have same index sets
    
model.OBJ = pe.Objective(rule = obj_rule, sense = pe.minimize)
# 'rule' should be a function with model as the only argument. Other option for sense: pe.maximize

# Other option is using 'expr' which means expression
#model.OBJ = pe.Objective( expr = pe.summation(model.cost, model.X),sense = pe.minimize )

#print the objective
model.OBJ.pprint()


#----------SOLVING----------

solver = pe.SolverFactory('cplex') # Specify Solver

# Finally, solve the model, change 'tee = False' to suppress the solver output
# Set 'tee = True' for a verbose output
# make 'keepfiles = False' to suppress file output
results = solver.solve(model, tee = True, keepfiles = False)

print()
# Check solver status, termination condition
#Ideally, Status should be 'ok' and termination condition 'optimal'
print("Status:", results.solver.status)
print("Termination Condition:", results.solver.termination_condition)


# ---------POST-PROCESSING-------------------

# Extract X values : model.X[<index>].value e.g.,
print(model.X[0,1].value)
print()

for f in model.facilities:
    for w in model.warehouses:
        if model.X[f,w].value != 0:
            print('Transport %d units from facility %d to warehouse %d'%(model.X[f,w].value,f,w))

print()
# print(dual values: model.dual[<constaint>] e.g. model.dual[model.CapacityCons[0]])
for f in model.facilities:
    print('Dual of',model.CapacityCons[f],':', model.dual[model.CapacityCons[f]])
    # Do same for DemandCons

# print(Objective function: model.OBJ())
print("\nObjective function value: ", model.OBJ())

# How to skip constraints for some elements in the index set?

# For the elements for which there is no constraint, the rule function should
# return pe.Constraint.Skip. Otherwise Pyomo will complain

# e.g., the constraint X[t] >= X[t-1] for t = 2,...,T (not t = 1) is coded as follows:

#def cons1_rule(model,t):
#    if t == 1:
#        return pe.Constraint.Skip
#    else:
#        return model.X[t] >= model.X[t-1]
#model.cons1 = pe.Constraint(model.time_periods,rule = cons1_rule)
#
# here model.time_periods is the set {1,2,...,T}
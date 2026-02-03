import gurobipy as gp
from gurobipy import GRB
import json 
import os
with open('cvrp_problem_data.json', 'r') as f:
    data = json.load(f)

#Reading data from JSON file 

N = int(data["nodes"]["total"]) #get total number of nodes
locations = [int(l) for l in data["nodes"]["delivery_locations"]] #get delivery locations excluding depot
n_vehicles = int(data["vehicles"]["count"]) #get number of vehicles
capacity = int(data["vehicles"]["capacity_per_vehicle"]) #get vehicles capacity 
vehicles = range(n_vehicles) #list of vehicles
demands = [int(d) for d in data["demands"]]  #get demands 
distances = [[int(d) for d in row] for row in data["distance_matrix"]] #get distance matrix

#Create a new model
model = gp.Model("CVRP")

#Decision Variables : 

# x[i][j][k] = 1 if vehicle k travels from node i to node j, 0 otherwise
x = model.addVars(N, N, n_vehicles, vtype=GRB.BINARY, name="x")
# y[i][k] = 1 if vehicle k delivers to location i, 0 otherwise
y = model.addVars(N, n_vehicles, vtype=GRB.BINARY, name="y")

#Constraints : 

#Each delivery location is visited exactly once
model.addConstrs((gp.quicksum(y[i,k] for k in vehicles) == 1 for i in locations), name="visit_once")

#Capacity Constraints 
model.addConstrs((gp.quicksum(demands[i]*y[i,k] for i in locations) <= capacity for k in vehicles), name="capacity")

#linking x and y variables : if a delivery location visisted by vehicle k then the vehicle arrives and departs from that location
model.addConstrs((gp.quicksum(x[i,j,k] for j in range(N) if j != i) == y[i,k] for i in locations for k in vehicles), name="linking_out") 
model.addConstrs((gp.quicksum(x[j,i,k] for j in range(N) if j != i) == y[i,k] for i in locations for k in vehicles), name="linking_in") 
   

#Flow conservation 
model.addConstrs(
    (gp.quicksum(x[i,j,k] for j in range(N) if j != i) ==gp.quicksum(x[j,i,k] for j in range(N) if j != i) for k in vehicles for i in locations),name="flow_conservation")

#Each vehicle starts and ends at the depot (node 0) aka enters depot once and leaves once , no trip from depot to depot
model.addConstrs((gp.quicksum(x[0,j,k] for j in range(1, N)) == 1 for k in vehicles), name="start_depot")
model.addConstrs((gp.quicksum(x[i,0,k] for i in range(1, N)) == 1 for k in vehicles), name="end_depot")
model.addConstrs((x[0, 0, k] == 0 for k in vehicles), name="no_depot_to_depot")

#Objective Function : Minimize total distance traveled by all vehicles
model.setObjective(gp.quicksum(distances[i][j] * x[i,j,k] for i in range(N) for j in range(N) for k in vehicles if i != j), GRB.MINIMIZE)

#Subtour elimination : Finding cycles that are not connected to the depot 
def find_subtours(x_vals, N, threshold=0.5, depot=0):
    """
    Find subtours (connected components not containing depot) from arc values.

    Parameters
    - x_vals: either
        * a 2D list/matrix-like (N x N) of values (x_vals[i][j]), or
        * a dict mapping (i,j) -> value.
    - N: number of nodes
    - threshold: consider arc present if value > threshold
    - depot: depot node index (default 0)

    Returns
    - List of sets, each a component (set of node indices) that does NOT contain the depot.
    """
    # build undirected adjacency from arcs above threshold
    adj = {i: set() for i in range(N)}
    def val(i, j):
        if isinstance(x_vals, dict):
            return x_vals.get((i, j), 0.0)
        return x_vals[i][j]

    for i in range(N):
        for j in range(N):
            if i != j and val(i, j) > threshold:
                adj[i].add(j)
                adj[j].add(i)

    # find connected components using DFS/BFS
    visited = set()
    subtours = []
    for start in range(0, N):
        if start in visited:
            continue
        stack = [start]
        comp = set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            visited.add(u)
            for v in adj[u]:
                if v not in comp:
                    stack.append(v)
        # report component if it doesn't include depot and has >1 node (optional)
        if comp and depot not in comp and len(comp) > 1:
            subtours.append(comp)
    return subtours

#Define a callback function to add subtour elimination constraints
def subtour_callback(model, where):
    if where == gp.GRB.Callback.MIPSOL:
        for k in vehicles:
            vals = {(i, j): model.cbGetSolution(x[i, j, k])
                    for i in range(N) for j in range(N)}
            subtours = find_subtours(vals, N, threshold=0.5, depot=0)
            for comp in subtours:
                # cut: sum_{i in S, j in S} x[i,j,k] <= |S| - 1
                expr = gp.quicksum(x[i, j, k] for i in comp for j in comp)
                model.cbLazy(expr <= len(comp) - 1)
                
#Optimize the model with the callback
model.Params.LazyConstraints = 1
model.optimize(subtour_callback)
def extract_routes(sol, N, vehicles, threshold=0.5):
    routes = {}
    for k in vehicles:
        cur = 0
        route = [0]
        visited = set()
        while True:
            next_nodes = [j for j in range(N) if j != cur and sol[cur, j, k] > threshold]
            if not next_nodes:
                raise RuntimeError(f"Vehicle {k}: no outgoing arc from {cur}")
            if len(next_nodes) > 1:
                raise RuntimeError(f"Vehicle {k}: branching at {cur} -> invalid solution")
            j = next_nodes[0]
            route.append(j)
            if j == 0:
                break
            if j in visited:
                raise RuntimeError(f"Vehicle {k}: cycle before depot: {route}")
            visited.add(j)
            cur = j
        routes[k] = route
    return routes

def route_stats(route, demands, distances):
    load = sum(demands[i] for i in route if i != 0)
    dist = sum(distances[route[i]][route[i+1]] for i in range(len(route)-1)) if len(route) > 1 else 0
    return load, dist


sol = model.getAttr('x', x)  # tuple-indexed solution
routes = extract_routes(sol, N, vehicles)
for k in vehicles:
    r = routes[k]
    load, dist = route_stats(r, demands, distances)
    print(f"Vehicle {k}: route={r} load={load} dist={dist}")
    if load > capacity + 1e-6:
            print(f"Capacity violation: Vehicle {k} load={load} > capacity={capacity}")
    else : 
        print(f"All vehicle loads are within capacity")


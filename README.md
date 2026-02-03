# Delivery Routing Assessment

## Objectives

The objective is to solve a **Capacitated Vehicle Routing Problem (CVRP)** with:

- One depot (node 0)
- 20 delivery locations
- Two identical vehicles with limited capacity
- Each delivery location served exactly once
- Each vehicle starting and ending at the depot
- Minimum total travel distance

---

## I. Problem Description

The Capacitated Vehicle Routing Problem (CVRP) consists of routing a fleet of vehicles with limited capacity from a central depot to serve customer locations with known demands.

**Problem data:**

- Depot: node 0
- Delivery locations: nodes listed in `locations`
- Total number of nodes: `N`
- Vehicles: `n_vehicles`
- Objective: minimize total travel distance

Nodes are indexed from `0` to `N−1`.

---

## II. Model Formulation

### 2.1 Index Sets (as used in code)

- **Nodes**: indices `i, j ∈ {0, …, N−1}`
- **Delivery locations**: `i ∈ locations` (excludes depot)
- **Vehicles**: `k ∈ {0, …, n_vehicles−1}`

---

### 2.2 Parameters

- `demands[i]`: demand at node `i` (with `demands[0] = 0`)
- `capacity`: maximum load per vehicle
- `distances[i][j]`: distance from node `i` to node `j`

---

### 2.3 Decision Variables

- `x[i][j][k] ∈ {0,1}`  
  Equals 1 if vehicle `k` travels directly from node `i` to node `j`

- `y[i][k] ∈ {0,1}`  
  Equals 1 if vehicle `k` services delivery location `i`

---

### 2.4 Objective Function

Minimize the total distance traveled by all vehicles:

$$
\min \sum_{k} \sum_{i=0}^{N-1} \sum_{j=0}^{N-1}
distances_{ij} \, x_{ijk}
$$

Self-loops (`i = j`) are explicitly forbidden by constraints.

---

### 2.5 Constraints

#### 1. Each Delivery Location Is Visited Exactly Once

Each delivery location must be assigned to exactly one vehicle.

$$
\sum_{k} y_{ik} = 1
$$

for every `i` in `locations`.

---

#### 2. Vehicle Capacity Constraints

The total demand assigned to a vehicle must not exceed its capacity.

$$
\sum_{i \in locations} demands_i \, y_{ik} \le capacity
$$

for every vehicle `k`.

---

#### 3. Linking Constraints (Flow–Assignment Consistency)

If a vehicle services a location, it must arrive at and depart from that location exactly once.

Outgoing flow:

$$
\sum_{j=0}^{N-1,\, j \neq i} x_{ijk} = y_{ik}
$$

Incoming flow:

$$
\sum_{j=0}^{N-1,\, j \neq i} x_{jik} = y_{ik}
$$

for every delivery location `i` and every vehicle `k`.

---

#### 4. Flow Conservation

For each delivery location and vehicle, incoming flow equals outgoing flow.

$$
\sum_{j=0}^{N-1} x_{ijk} = \sum_{j=0}^{N-1} x_{jik}
$$

for every delivery location `i` and every vehicle `k`.

---

#### 5. Depot Constraints

Each vehicle starts and ends at the depot (node 0).

Exactly one departure from the depot:

$$
\sum_{j=1}^{N-1} x_{0jk} = 1
$$

Exactly one return to the depot:

$$
\sum_{i=1}^{N-1} x_{i0k} = 1
$$

No depot-to-depot travel:

$$
x_{00k} = 0
$$

for every vehicle `k`.

---

#### 6. Subtour Elimination (Lazy Constraints)

To prevent cycles that do not include the depot, subtours are eliminated dynamically.

For any subset `S` of nodes forming a cycle that does **not** include node 0:

$$
\sum_{i \in S} \sum_{j \in S} x_{ijk} \le |S| - 1
$$

for the corresponding vehicle `k`.

These constraints are added during optimization using a Gurobi callback.

---

## III. Model Properties

This formulation ensures that:

- Every delivery location is served exactly once
- Vehicle capacity limits are respected
- Each vehicle route starts and ends at the depot
- Subtours disconnected from the depot are eliminated
- Total travel distance is minimized

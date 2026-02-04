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
- Delivery locations: nodes listed in locations set
- Total number of nodes: $N$
- Number of vehicles: $n_{\text{vehicles}}$
- Objective: minimize total travel distance

Nodes are indexed from $0$ to $N-1$.

---

## II. Model Formulation

### 2.1 Index Sets (as used in code)

- **Nodes**: indices $i, j \in \{0, \ldots, N-1\}$
- **Delivery locations**: $i \in \text{locations}$ (excludes depot)
- **Vehicles**: $k \in \{0, \ldots, n_{\text{vehicles}}-1\}$

---

### 2.2 Parameters

- $\text{demands}_i$: demand at node $i$ (with $\text{demands}_0 = 0$)
- $\text{capacity}$: maximum load per vehicle
- $\text{distances}_{ij}$: distance from node $i$ to node $j$

---

### 2.3 Decision Variables

- $x_{ijk} \in \{0,1\}$  
  Equals 1 if vehicle $k$ travels directly from node $i$ to node $j$

- $y_{ik} \in \{0,1\}$  
  Equals 1 if vehicle $k$ services delivery location $i$

---

### 2.4 Objective Function

Minimize the total distance traveled by all vehicles:

$$
\min \sum_{k} \sum_{i=0}^{N-1} \sum_{\substack{j=0 \\ j \neq i}}^{N-1} \text{distances}_{ij} \cdot x_{ijk}
$$

Self-loops ($i = j$) are explicitly forbidden by constraints.

---

### 2.5 Constraints

#### 1. Each Delivery Location Is Visited Exactly Once

Each delivery location must be assigned to exactly one vehicle.

$$
\sum_{k} y_{ik} = 1 \quad \forall i \in \text{locations}
$$

---

#### 2. Vehicle Capacity Constraints

The total demand assigned to a vehicle must not exceed its capacity.

$$
\sum_{i \in \text{locations}} \text{demands}_i \cdot y_{ik} \le \text{capacity} \quad \forall k
$$

---

#### 3. Linking Constraints (Flow–Assignment Consistency)

If a vehicle services a location, it must arrive at and depart from that location exactly once.

Outgoing flow:

$$
\sum_{\substack{j=0 \\ j \neq i}}^{N-1} x_{ijk} = y_{ik} \quad \forall i \in \text{locations}, \, \forall k
$$

Incoming flow:

$$
\sum_{\substack{j=0 \\ j \neq i}}^{N-1} x_{jik} = y_{ik} \quad \forall i \in \text{locations}, \, \forall k
$$

---

#### 4. Flow Conservation

For each delivery location and vehicle, incoming flow equals outgoing flow.

$$
\sum_{\substack{j=0 \\ j \neq i}}^{N-1} x_{ijk} = \sum_{\substack{j=0 \\ j \neq i}}^{N-1} x_{jik} \quad \forall i \in \text{locations}, \, \forall k
$$

---

#### 5. Depot Constraints

Each vehicle starts and ends at the depot (node 0).

Exactly one departure from the depot:

$$
\sum_{j=1}^{N-1} x_{0jk} = 1 \quad \forall k
$$

Exactly one return to the depot:

$$
\sum_{i=1}^{N-1} x_{i0k} = 1 \quad \forall k
$$

No depot-to-depot travel:

$$
x_{00k} = 0 \quad \forall k
$$

---

#### 6. Subtour Elimination (Lazy Constraints)

To prevent cycles that do not include the depot, subtours are eliminated dynamically.

For any subset $S$ of nodes forming a cycle that does **not** include node 0:

$$
\sum_{i \in S} \sum_{j \in S} x_{ijk} \le |S| - 1
$$

for the corresponding vehicle $k$.

These constraints are added during optimization using a Gurobi callback.

This formulation ensures that:

- Every delivery location is served exactly once
- Vehicle capacity limits are respected
- Each vehicle route starts and ends at the depot
- Subtours disconnected from the depot are eliminated
- Total travel distance is minimized

---

## III. Variable Choices and Alternative Formulations

The implemented model uses a **three-index arc-based formulation** with binary variables $x_{ijk}$ for routing decisions and auxiliary variables $y_{ik}$ for assignment tracking. This formulation is intuitive and explicitly models vehicle-specific routes, making it well-suited for problems with a small to moderate number of vehicles. Subtour elimination is handled dynamically through lazy constraints, which keeps the initial model size manageable.

**Alternative formulations** that could be considered include:

- **Miller-Tucker-Zemlin (MTZ) formulation**: Introduces continuous variables $u_i$ representing the position of each node in the tour sequence. Subtour elimination is enforced through constraints of the form $u_i - u_j + N \cdot x_{ijk} \le N-1$, avoiding the need for exponentially many subtour constraints or callbacks. However, MTZ constraints can be weaker from a linear relaxation perspective.

- **Two-index (vehicle-aggregated) formulation**: Uses variables $x_{ij}$ without the vehicle index, suitable when vehicles are identical and route-to-vehicle assignment is not critical. This reduces model size but may complicate capacity tracking.

- **Set partitioning/covering formulation**: Pre-enumerates all feasible routes and uses binary variables for route selection. This formulation typically provides strong linear relaxations but is computationally expensive for large instances due to the exponential number of potential routes, often requiring column generation techniques.

Each formulation presents trade-offs between model size, relaxation strength, and implementation complexity, with the choice depending on instance characteristics and computational resources.

---

## IV. How to Run

### 4.1 Prerequisites

- **Python 3.8+**
- **Gurobi Optimizer** (version 9.0 or higher)
  - Requires a valid Gurobi license 
- **gurobipy** Python package

### 4.2 Installation

1. Install Gurobi

2. Install the required Python package:
```bash
pip install gurobipy
```

### 4.3 Running the Code

1. Ensure `cvrp_problem_data.json` is in the same directory as `CVRP.py`

2. Run the optimization:
```bash
python CVRP.py
```

The script will:
- Load problem data from the JSON file
- Build and solve the CVRP model
- Output the optimal routes for each vehicle with load and distance information

---

## V. Results

### 5.1 Optimal Solution

The optimization achieved an **optimal solution** with a total travel distance of **215 units**.

**Vehicle 0:**
- Route: 0 → 5 → 14 → 6 → 10 → 9 → 19 → 13 → 4 → 3 → 1 → 0
- Total load: 92 units (within capacity of 100)
- Distance traveled: 106 units

**Vehicle 1:**
- Route: 0 → 2 → 20 → 15 → 16 → 18 → 7 → 8 → 17 → 12 → 11 → 0
- Total load: 98 units (within capacity of 100)
- Distance traveled: 109 units

### 5.2 Computational Performance

- **Optimization time:** 144.10 seconds
- **Nodes explored:** 101,642
- **Optimality gap:** 0.0% (proven optimal)
- **Lazy constraints added:** 5,020 (for subtour elimination)

Both vehicles operate near full capacity (92% and 98% utilization), demonstrating efficient load distribution across the fleet.

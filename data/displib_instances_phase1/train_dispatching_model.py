import json
from gurobipy import Model, GRB, quicksum

# Load the instance file
with open("line3_1.json", "r") as f:
    data = json.load(f)

trains = data["trains"]
BIG_M = 1e6

# Initialize model
model = Model("TrainDispatching_Metrics")

# Decision variables
start = {}  # Start time of each operation
delay = {}  # Delay per train
ops = []    # List of all (i, j) pairs

# Create variables
for i, train in enumerate(trains):
    for j, op in enumerate(train):
        lb = op.get("start_lb", 0)
        start[(i, j)] = model.addVar(lb=lb, vtype=GRB.CONTINUOUS, name=f"t_{i}_{j}")
        ops.append((i, j))
    delay[i] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"delay_{i}")

model.update()

# Precedence constraints within trains
for i, train in enumerate(trains):
    for j, op in enumerate(train):
        for succ in op.get("successors", []):
            dur = op.get("min_duration", 0)
            model.addConstr(start[(i, succ)] >= start[(i, j)] + dur, name=f"prec_{i}_{j}_{succ}")

# Delay definition: delay >= actual end - planned end
for i, train in enumerate(trains):
    last = len(train) - 1
    lb_last = train[last].get("start_lb", 0)
    model.addConstr(delay[i] >= start[(i, last)] - lb_last, name=f"delay_{i}")

# Resource conflict constraints
y = {}
for idx1 in range(len(ops)):
    i1, j1 = ops[idx1]
    res1 = {r["resource"] for r in trains[i1][j1].get("resources", [])}
    for idx2 in range(idx1 + 1, len(ops)):
        i2, j2 = ops[idx2]
        if i1 == i2:
            continue
        res2 = {r["resource"] for r in trains[i2][j2].get("resources", [])}
        common = res1.intersection(res2)
        if common:
            y_var = model.addVar(vtype=GRB.BINARY, name=f"y_{i1}_{j1}_{i2}_{j2}")
            y[(i1, j1, i2, j2)] = y_var
            dur1 = trains[i1][j1].get("min_duration", 0)
            dur2 = trains[i2][j2].get("min_duration", 0)

            model.addConstr(start[(i1, j1)] + dur1 <= start[(i2, j2)] + BIG_M * (1 - y_var),
                            name=f"before_{i1}_{j1}_{i2}_{j2}")
            model.addConstr(start[(i2, j2)] + dur2 <= start[(i1, j1)] + BIG_M * y_var,
                            name=f"after_{i2}_{j2}_{i1}_{j1}")

model.update()

# Objective: minimize total delay
model.setObjective(quicksum(delay[i] for i in delay), GRB.MINIMIZE)

# Solve the model
model.optimize()

# Output: individual delays
print("\nIndividual delays:")
for i in sorted(delay.keys()):
    print(f"Train {i}: Delay = {delay[i].X:.2f}")

# Output: metrics
total_delay = sum(delay[i].X for i in delay)
average_delay = total_delay / len(delay)
max_delay = max(delay[i].X for i in delay)

print("\n--- Delay Metrics ---")
print(f"Total delay:   {total_delay:.2f}")
print(f"Average delay: {average_delay:.2f}")
print(f"Max delay:     {max_delay:.2f}")
# master_model.py (mit Pfadwahl erweitert)
from gurobipy import Model, GRB

def solve_master(data, cuts):
    model = Model("master_problem")
    model.setParam("OutputFlag", 0)

    trains = data["trains"]
    paths = data["paths"]  # dict: train_id -> list of paths
    conflicts = data["conflicts"]  # list of (train1, op1, train2, op2)
    no_swaps = data.get("no_swaps", [])

    # Variablen: Pfadwahl z_{tp}
    z = {}
    for t, t_paths in paths.items():
        for p_id in range(len(t_paths)):
            z[(int(t), p_id)] = model.addVar(vtype=GRB.BINARY, name=f"z_{t}_{p_id}")

    # Variablen: Reihenfolge x_{ij}
    x = {}
    for (t1, o1, t2, o2) in conflicts:
        x[(t1, o1, t2, o2)] = model.addVar(vtype=GRB.BINARY, name=f"x_{t1}_{o1}_{t2}_{o2}")

    # Consistent ordering on shared resource sequences
    for pair1, pair2 in no_swaps:
        if pair1 in x and pair2 in x:
            model.addConstr(x[pair1] == x[pair2], name=f"noswap_{pair1}_{pair2}")

    # Pfadwahl: genau ein Pfad je Zug
    for t in paths:
        model.addConstr(sum(z[(int(t), p)] for p in range(len(paths[t]))) == 1, name=f"choose_path_{t}")

    # Bestehende Cuts einbauen
    for c in cuts:
        model.addConstr(sum(x[key] for key in c) <= len(c) - 1, name=f"cut_{len(cuts)}")

    model.setObjective(0, GRB.MINIMIZE)  # Dummy-Ziel
    model.optimize()

    # Export only chosen paths but keep all ordering decisions
    z_sol = {k: int(round(v.X)) for k, v in z.items() if v.X > 0.5}
    x_sol = {k: int(round(v.X)) for k, v in x.items()}
    return {"z": z_sol, "x": x_sol}

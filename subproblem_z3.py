# subproblem_z3.py (nutzt train.operations korrekt)
from z3 import Real, Solver

def check_feasibility(data, solution):
    solver = Solver()
    trains = data["train_objects"]  # erwartet Liste von Train-Objekten
    paths = data["paths"]
    durations = data["durations"]

    S = {}
    W = {}
    R_rel = {}

    for (t, p_id), val in solution["z"].items():
        path = paths[str(t)][p_id]
        for o in path:
            key = (t, o)
            S[key] = Real(f"S_{t}_{o}")
            W[key] = Real(f"W_{t}_{o}")
            solver.add(W[key] >= 0)

            op_data = trains[t].operations[o]
            lb = op_data.start_lb if op_data.start_lb is not None else 0
            solver.add(S[key] >= lb)
            if op_data.start_ub is not None:
                solver.add(S[key] <= op_data.start_ub)

    for (t, p_id), val in solution["z"].items():
        path = paths[str(t)][p_id]
        for i in range(len(path)):
            o = path[i]
            key = (t, o)
            dur = durations[str(key)]
            if i < len(path) - 1:
                o_succ = path[i + 1]
                key_succ = (t, o_succ)
                solver.add(S[key_succ] >= S[key] + dur + W[key])

                op_data = trains[t].operations[o]
                for r in op_data.resources:
                    rel = r.get("release_time", 0)
                    R_rel[(t, o, r["resource"])] = (key_succ, rel)
            else:
                op_data = trains[t].operations[o]
                for r in op_data.resources:
                    R_rel[(t, o, r["resource"])] = (key, 0)

    for (t1, p_id1), val1 in solution["z"].items():
        for o1 in paths[str(t1)][p_id1]:
            op1 = trains[t1].operations[o1]
            for r1 in op1.resources:
                rname = r1["resource"]
                key1 = (t1, o1, rname)
                if key1 not in R_rel: continue
                release_key1, rel1 = R_rel[key1]
                for (t2, p_id2), val2 in solution["z"].items():
                    for o2 in paths[str(t2)][p_id2]:
                        if (t1 == t2 and o1 == o2): continue
                        op2 = trains[t2].operations[o2]
                        for r2 in op2.resources:
                            if r2["resource"] == rname:
                                key2 = (t2, o2)
                                release_key2, rel2 = R_rel.get((t2, o2, rname), (key2, 0))
                                solver.add(
                                    (S[release_key1] + rel1 <= S[key2]) 
                                    | (S[release_key2] + rel2 <= S[(t1, o1)])
                                )

    result = solver.check()
    if result.r == 1:
        model = solver.model()
        x_vals_result = {key: float(model[S[key]].as_decimal(5).replace("?", "")) for key in S}
        return True, 0.0, x_vals_result
    else:
        return False, None, None

import gurobipy as gp
from gurobipy import GRB
import json
import matplotlib.pyplot as plt

# --- Eingabe ---
with open('line3_2.json', 'r') as f:
    data = json.load(f)

trains     = data['trains']
objectives = data['objective']

# --- Modell ---
model       = gp.Model('Train_Dispatching')
BIG_M       = 1_000_000

# Variablen
s        = {}  # Startzeiten
delay    = {}  # Verzögerungen
is_late  = {}  # Binär für Sprungkosten
z        = {}  # Reihenfolge-Binärvariablen für Ressourcenkonflikte

# Vorverarbeitung
operations = []
resources  = {}
successors = {}

for t_id, ops in enumerate(trains):
    for o_id, op in enumerate(ops):
        operations.append((t_id, o_id))
        successors[(t_id, o_id)] = op.get('successors', [])
        for r in op.get('resources', []):
            resources.setdefault(r['resource'], []).append((t_id, o_id))

# s als Integer-Var. (DISPLIB verlangt ganzzahlige Zeitpunkte)
for (t_id, o_id) in operations:
    s[(t_id, o_id)] = model.addVar(lb=0, vtype=GRB.INTEGER,
                                   name=f'start_{t_id}_{o_id}')

# Delay-Variablen + optional Binär
for obj in objectives:
    key = (obj['train'], obj['operation'])
    delay[key] = model.addVar(lb=0, vtype=GRB.CONTINUOUS,
                              name=f'delay_{key[0]}_{key[1]}')
    if obj.get('increment', 0) > 0:
        is_late[key] = model.addVar(vtype=GRB.BINARY,
                                    name=f'is_late_{key[0]}_{key[1]}')

model.update()

# --- Constraints ---

# a) Startzeit-Bounds
for (t_id, o_id) in operations:
    op = trains[t_id][o_id]
    if 'start_lb' in op:
        model.addConstr(s[(t_id, o_id)] >= op['start_lb'],
                        name=f'start_lb_{t_id}_{o_id}')
    if 'start_ub' in op:
        model.addConstr(s[(t_id, o_id)] <= op['start_ub'],
                        name=f'start_ub_{t_id}_{o_id}')

# b) Precedence innerhalb eines Zuges
for (t_id, o_id), succ_list in successors.items():
    dur = trains[t_id][o_id]['min_duration']
    for succ_id in succ_list:
        model.addConstr(
            s[(t_id, o_id)] + dur <= s[(t_id, succ_id)],
            name=f'prec_{t_id}_{o_id}_to_{t_id}_{succ_id}'
        )

# c) Ressourcenkonflikte nur zwischen verschiedenen Zügen
for res, ops in resources.items():
    for i in range(len(ops)):
        for j in range(i+1, len(ops)):
            op1 = ops[i]
            op2 = ops[j]
            # nur, wenn es verschiedene Züge sind
            if op1[0] == op2[0]:
                continue

            # Binärvar. für Reihenfolge
            z[(op1, op2)] = model.addVar(vtype=GRB.BINARY,
                                         name=f'z_{op1[0]}_{op1[1]}_{op2[0]}_{op2[1]}')

            # effektive Dauern inkl. Release-Time
            rel1 = next(r.get('release_time', 0)
                        for r in trains[op1[0]][op1[1]]['resources']
                        if r['resource'] == res)
            rel2 = next(r.get('release_time', 0)
                        for r in trains[op2[0]][op2[1]]['resources']
                        if r['resource'] == res)
            dur1 = trains[op1[0]][op1[1]]['min_duration'] + rel1
            dur2 = trains[op2[0]][op2[1]]['min_duration'] + rel2

            # Entweder op1 vor op2 …
            model.addConstr(
                s[op1] + dur1 <= s[op2] + BIG_M*(1 - z[(op1, op2)]),
                name=f'res_{res}_ord1_{op1}_{op2}'
            )
            # … oder umgekehrt
            model.addConstr(
                s[op2] + dur2 <= s[op1] + BIG_M*z[(op1, op2)],
                name=f'res_{res}_ord2_{op1}_{op2}'
            )

# d) Verzögerungs-Definition auf Startzeit (DISPLIB misst delay an s, nicht Fertigstellung)
for obj in objectives:
    t_id = obj['train']
    o_id = obj['operation']
    thr  = obj.get('threshold', 0)
    key  = (t_id, o_id)

    # delay ≥ s − threshold
    model.addConstr(
        delay[key] >= s[key] - thr,
        name=f'delay_def_{t_id}_{o_id}'
    )
    # delay ≥ 0
    model.addConstr(
        delay[key] >= 0,
        name=f'delay_nonneg_{t_id}_{o_id}'
    )

    # Sprungkosten-Verknüpfung
    if key in is_late:
        model.addConstr(
            s[key] - thr <= BIG_M * is_late[key],
            name=f'is_late_def_{t_id}_{o_id}'
        )

# --- Zielfunktion ---
obj_expr = gp.quicksum(
    obj.get('coeff', 0) * delay[(obj['train'], obj['operation'])] +
    obj.get('increment', 0) * is_late.get((obj['train'], obj['operation']), 0)
    for obj in objectives
)
model.setObjective(obj_expr, GRB.MINIMIZE)

# --- Optimierung starten ---
model.optimize()

# --- Ergebnisse ausgeben ---
if model.status == GRB.OPTIMAL:
    print("\n--- Startzeiten ---")
    for (t_id, o_id) in operations:
        print(f"Zug {t_id}, Op {o_id}: Start = {s[(t_id, o_id)].X}")

    print(f"\nOptimale Kosten: {model.ObjVal:.2f}\n")

    # Verzögerungen pro Zug
    total_delay = {}
    for (t_id, o_id), var in delay.items():
        total_delay.setdefault(t_id, 0.0)
        total_delay[t_id] += var.X

    print("--- Gesamtverzögerung je Zug ---")
    for t_id, dsum in total_delay.items():
        print(f"Zug {t_id}: {dsum:.2f}")

    print("\n--- Statistik ---")
    delays = list(total_delay.values())
    print(f"Total: {sum(delays):.2f}")
    print(f"Durchschnitt: {sum(delays)/len(delays):.2f}")
    print(f"Maximal: {max(delays):.2f}")
else:
    print("Kein optimales Ergebnis gefunden. Statuscode:", model.status)
import gurobipy as gp
from gurobipy import GRB
import json
import matplotlib.pyplot as plt

# --- Eingabe ---
with open('line3_2.json', 'r') as f:
    data = json.load(f)

trains = data['trains']
objectives = data['objective']

# --- Modell ---
model = gp.Model('Train_Dispatching')

operations = []
resources = dict()
successors = dict()
s = dict()
z = dict()
delay = dict()
is_late = dict()

# --- Vorverarbeitung ---
for train_id, ops in enumerate(trains):
    for op_id, op in enumerate(ops):
        operations.append((train_id, op_id))
        if 'resources' in op:
            for r in op['resources']:
                res_name = r['resource']
                if res_name not in resources:
                    resources[res_name] = []
                resources[res_name].append((train_id, op_id))
        successors[(train_id, op_id)] = [(train_id, succ_id) for succ_id in op['successors']]

# --- Variablen ---
for (train_id, op_id) in operations:
    s[(train_id, op_id)] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f'start_{train_id}_{op_id}')

for obj in objectives:
    key = (obj['train'], obj['operation'])
    delay[key] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f'delay_{key[0]}_{key[1]}')
    if 'increment' in obj:
        is_late[key] = model.addVar(vtype=GRB.BINARY, name=f'is_late_{key[0]}_{key[1]}')

model.update()

BIG_M = 1e6

# --- Constraints ---

# a) Startzeit-Beschränkungen
for train_id, ops in enumerate(trains):
    for op_id, op in enumerate(ops):
        if 'start_lb' in op:
            model.addConstr(s[(train_id, op_id)] >= op['start_lb'], name=f'start_lb_{train_id}_{op_id}')
        if 'start_ub' in op:
            model.addConstr(s[(train_id, op_id)] <= op['start_ub'], name=f'start_ub_{train_id}_{op_id}')

# b) Precedence innerhalb eines Zuges
for (train_id, op_id), succ_list in successors.items():
    for (succ_train_id, succ_op_id) in succ_list:
        p_duration = trains[train_id][op_id]['min_duration']
        model.addConstr(
            s[(train_id, op_id)] + p_duration <= s[(succ_train_id, succ_op_id)],
            name=f'prec_{train_id}_{op_id}_to_{succ_train_id}_{succ_op_id}'
        )

# c) Ressourcenkonflikte mit Release Times
for res, ops in resources.items():
    for i in range(len(ops)):
        for j in range(i+1, len(ops)):
            op1 = ops[i]
            op2 = ops[j]
            z[(op1, op2)] = model.addVar(vtype=GRB.BINARY, name=f'z_{op1[0]}_{op1[1]}_{op2[0]}_{op2[1]}')

            release_time_op1 = next(r.get('release_time', 0) for r in trains[op1[0]][op1[1]]['resources'] if r['resource'] == res)
            release_time_op2 = next(r.get('release_time', 0) for r in trains[op2[0]][op2[1]]['resources'] if r['resource'] == res)

            dur1 = trains[op1[0]][op1[1]]['min_duration'] + release_time_op1
            dur2 = trains[op2[0]][op2[1]]['min_duration'] + release_time_op2

            model.addConstr(
                s[op1] + dur1 <= s[op2] + BIG_M * (1 - z[(op1, op2)]),
                name=f'res_conf_1_{op1[0]}_{op1[1]}_{op2[0]}_{op2[1]}'
            )
            model.addConstr(
                s[op2] + dur2 <= s[op1] + BIG_M * z[(op1, op2)],
                name=f'res_conf_2_{op1[0]}_{op1[1]}_{op2[0]}_{op2[1]}'
            )

model.update()

# d) Delay Constraints
for obj in objectives:
    train_id = obj['train']
    op_id = obj['operation']
    threshold = obj['threshold']
    p_duration = trains[train_id][op_id]['min_duration']

    model.addConstr(
        delay[(train_id, op_id)] >= (s[(train_id, op_id)] + p_duration) - threshold,
        name=f'delay_def_{train_id}_{op_id}'
    )
    model.addConstr(
        delay[(train_id, op_id)] >= 0,
        name=f'delay_nonneg_{train_id}_{op_id}'
    )

    if 'increment' in obj:
        model.addConstr(
            s[(train_id, op_id)] + p_duration - threshold <= BIG_M * is_late[(train_id, op_id)],
            name=f'is_late_def_{train_id}_{op_id}'
        )

# --- Zielfunktion ---
model.setObjective(
    gp.quicksum(
        (obj.get('coeff', 0)) * delay[(obj['train'], obj['operation'])] +
        (obj.get('increment', 0)) * is_late.get((obj['train'], obj['operation']), 0)
        for obj in objectives
    ),
    GRB.MINIMIZE
)

# --- Optimierung starten ---
model.optimize()

# --- Ergebnisse ---
if model.status == GRB.OPTIMAL:
    # Startzeiten
    for (train_id, op_id) in operations:
        print(f'Train {train_id}, Operation {op_id}: Startzeit = {s[(train_id, op_id)].X}')
    
    print(f"\nOptimale Gesamtkosten: {model.ObjVal:.2f}\n")

    # Verzögerungen
    total_delay = dict()
    for (train_id, op_id), var in delay.items():
        if train_id not in total_delay:
            total_delay[train_id] = 0
        total_delay[train_id] += var.X

    print("--- Verzögerungen je Zug ---")
    for train_id in sorted(total_delay.keys()):
        print(f"Zug {train_id}: Gesamtverzögerung = {total_delay[train_id]:.2f}")

    print("\n--- Zusammenfassung ---")
    total_delay_sum = sum(total_delay.values())
    average_delay = total_delay_sum / len(total_delay) if total_delay else 0
    max_delay = max(total_delay.values()) if total_delay else 0

    print(f"Totale Verzögerung: {total_delay_sum:.2f}")
    print(f"Durchschnittliche Verzögerung pro Zug: {average_delay:.2f}")
    print(f"Maximale Verzögerung eines Zuges: {max_delay:.2f}")

'''
# --- Gantt Chart ---
gantt_data = []

for (train_id, op_id) in operations:
    start = s[(train_id, op_id)].X
    duration = trains[train_id][op_id]['min_duration']
    gantt_data.append((train_id, op_id, start, duration))

gantt_data.sort(key=lambda x: x[2])

train_colors = plt.cm.get_cmap('tab20', len(set(train_id for train_id, _, _, _ in gantt_data)))

plt.figure(figsize=(14, 8))

for idx, (train_id, op_id, start, duration) in enumerate(gantt_data):
    plt.barh(train_id, duration, left=start, height=0.4, color=train_colors(train_id))
    if duration >= 10:
        plt.text(start + duration/2, train_id, f'{op_id}', va='center', ha='center', fontsize=5, color='white')

plt.xlabel('Zeit')
plt.ylabel('Zug-ID')
plt.title('Gantt-Chart der Zugoperationen')
plt.grid(True, axis='x')
plt.yticks(sorted(set(train_id for train_id, _, _, _ in gantt_data)))
plt.tight_layout()
plt.show()
'''
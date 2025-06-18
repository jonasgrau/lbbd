# lbbd_main.py
# Hauptsteuerung: Logic-Based Benders Decomposition für DISPLIB

from master_model import solve_master
from subproblem_z3 import check_feasibility
from cuts import generate_cut, export_solution
from utils import parse_displib_instance
import os

# Lade Instanz
instance = parse_displib_instance("/Users/jonas/Opti Lab/LBBD/data/displib_testinstances_headway1.json")
data = {
    "trains": list(range(len(instance.trains))),
    "train_objects": instance.trains,
    "paths": instance.generate_paths_dict(),
    "durations": {
        str((op.train_id, op.op_id)): op.min_duration
        for train in instance.trains for op in train.operations
    },
    "conflicts": instance.get_conflicts(),
    "objective": instance.objectives
}

# LBBD-Schleife
cuts = []
iteration = 0
best_solution = None
best_obj = float("inf")

while True:
    print(f"\n--- LBBD Iteration {iteration} ---")
    master_solution = solve_master(data, cuts)

    feasible, sub_obj, x_vals = check_feasibility(data, master_solution)
    if feasible:
        print("Gültige Zeitplanung gefunden.")
        if sub_obj < best_obj:
            best_obj = sub_obj
            best_solution = (x_vals, sub_obj)
        break
    else:
        print("Konflikt erkannt, Cut wird erzeugt...")
        new_cut = generate_cut(master_solution["x"].keys())
        cuts.append(new_cut)
        iteration += 1

# Exportiere Lösung
if best_solution:
    os.makedirs("output", exist_ok=True)
    export_solution(best_solution[0], best_solution[1], "output/solution_output.json")
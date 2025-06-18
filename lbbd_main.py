"""Entry point for running the LBBD train dispatching model."""

import argparse
import os

from master_model import solve_master
from subproblem_z3 import check_feasibility
from cuts import generate_cut, export_solution
from utils import parse_displib_instance, instance_to_data


ndefault = "data/displib_testinstances_headway1.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a DISPLIB instance using LBBD")
    parser.add_argument("instance", nargs="?", default=ndefault,
                        help="Path to a DISPLIB JSON instance file")
    parser.add_argument("--output", default="output/solution_output.json",
                        help="Where to write the resulting solution JSON")
    args = parser.parse_args()

    instance = parse_displib_instance(args.instance)
    data = instance_to_data(instance)

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

    if best_solution:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        export_solution(best_solution[0], best_solution[1], args.output)


if __name__ == "__main__":
    main()

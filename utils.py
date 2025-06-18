# utils.py (erweitert: generiert Pfade automatisch)
import json
from model import Operation, Train, DisplibInstance

def parse_displib_instance(path):
    with open(path) as f:
        raw = json.load(f)

    trains = []
    for t_id, op_list in enumerate(raw["trains"]):
        ops = []
        for o_id, op in enumerate(op_list):
            ops.append(Operation(
                train_id=t_id,
                op_id=o_id,
                min_duration=op["min_duration"],
                resources=op.get("resources", []),
                successors=op.get("successors", []),
                start_lb=op.get("start_lb"),
                start_ub=op.get("start_ub")
            ))
        trains.append(Train(train_id=t_id, operations=ops))

    objectives = raw.get("objective", [])
    instance = DisplibInstance(trains=trains, objectives=objectives)
    return instance

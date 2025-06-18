"""Utility helpers for DISPLIB instances."""

import json
from model import Operation, Train, DisplibInstance


def parse_displib_instance(path: str) -> DisplibInstance:
    """Parse a DISPLIB JSON instance file."""
    with open(path) as f:
        raw = json.load(f)

    trains = []
    for t_id, op_list in enumerate(raw["trains"]):
        ops = []
        for o_id, op in enumerate(op_list):
            ops.append(
                Operation(
                    train_id=t_id,
                    op_id=o_id,
                    min_duration=op["min_duration"],
                    resources=op.get("resources", []),
                    successors=op.get("successors", []),
                    start_lb=op.get("start_lb"),
                    start_ub=op.get("start_ub"),
                )
            )
        trains.append(Train(train_id=t_id, operations=ops))

    objectives = raw.get("objective", [])
    return DisplibInstance(trains=trains, objectives=objectives)


def instance_to_data(instance: DisplibInstance) -> dict:
    """Convert a :class:`DisplibInstance` to the data dictionary used by the models."""
    return {
        "trains": list(range(len(instance.trains))),
        "train_objects": instance.trains,
        "paths": instance.generate_paths_dict(),
        "durations": {
            str((op.train_id, op.op_id)): op.min_duration
            for train in instance.trains for op in train.operations
        },
        "conflicts": instance.get_conflicts(),
        "no_swaps": instance.get_no_swap_pairs(),
        "objective": instance.objectives,
    }

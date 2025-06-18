import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import parse_displib_instance, instance_to_data
pytest.importorskip('z3')
from subproblem_z3 import check_feasibility


def test_start_lb_enforced(tmp_path):
    fixture = tmp_path / "lb_instance.json"
    fixture.write_text(
        '{"trains": [[{"start_lb": 5, "min_duration": 1, "successors": [1]},'
        '{"min_duration": 1, "successors": []}]], "objective": []}'
    )
    instance = parse_displib_instance(str(fixture))
    data = instance_to_data(instance)
    solution = {"z": {(0, 0): 1}, "x": {}}
    feasible, _, times = check_feasibility(data, solution)
    assert feasible
    assert times[(0, 0)] >= 5

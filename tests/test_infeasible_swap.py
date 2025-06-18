import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import parse_displib_instance, instance_to_data
pytest.importorskip('z3')
from subproblem_z3 import check_feasibility


def test_infeasible_resource_swap():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'data',
                           'displib_testinstances_infeasible2.json')
    instance = parse_displib_instance(fixture)
    data = instance_to_data(instance)

    # Enforce same ordering on both resources
    solution = {
        'z': {(0, 0): 1, (1, 0): 1},
        'x': {(0, 0, 1, 1): 1, (0, 1, 1, 0): 1}
    }
    feasible, _, _ = check_feasibility(data, solution)
    assert not feasible

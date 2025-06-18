import os
import sys
import pytest

pytest.importorskip('z3')
pytest.importorskip('gurobipy')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import parse_displib_instance, instance_to_data
from master_model import solve_master
from subproblem_z3 import check_feasibility


def test_two_train_swap_infeasible():
    fixture = os.path.join(os.path.dirname(__file__), 'fixtures', 'swap_infeasible.json')
    instance = parse_displib_instance(fixture)
    data = instance_to_data(instance)
    master_solution = solve_master(data, [])
    feasible, _, _ = check_feasibility(data, master_solution)
    assert not feasible

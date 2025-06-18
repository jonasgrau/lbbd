import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import parse_displib_instance


def test_three_train_cycle_no_swaps():
    fixture = os.path.join(os.path.dirname(__file__), 'fixtures', 'triple_cycle.json')
    instance = parse_displib_instance(fixture)
    pairs = instance.get_no_swap_pairs()
    expected = [
        ((0, 1, 1, 1), (1, 0, 2, 1)),
        ((0, 2, 2, 0), (0, 1, 1, 1)),
        ((1, 0, 2, 1), (0, 2, 2, 0)),
    ]
    assert pairs == expected

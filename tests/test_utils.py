import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import parse_displib_instance


def test_parse_simple_instance():
    fixture = os.path.join(os.path.dirname(__file__), 'fixtures', 'simple_instance.json')
    data = parse_displib_instance(fixture)

    assert data['trains'] == [0, 1]
    assert data['paths']['0'] == [[0, 1]]
    assert data['paths']['1'] == [[0, 1]]
    assert data['durations']['(0, 1)'] == 2
    assert {(tuple(c) if isinstance(c, list) else c) for c in data['conflicts']} == {(0, 1, 1, 1)}

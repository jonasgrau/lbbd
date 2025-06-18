# cuts.py (ergänzt um JSON-Exportfunktion)
import json

def generate_cut(orderings):
    """Generate a cut from the current ordering decisions.

    ``orderings`` is a dict mapping conflict tuples ``(t1,o1,t2,o2)`` to a
    binary value.  ``1`` means ``(t1,o1)`` should occur before ``(t2,o2)`` and
    ``0`` the opposite.  Instead of returning all orderings (a simple no-good
    cut), we try to find a directed cycle implied by these decisions.  Only the
    edges in such a cycle are returned, which results in a much stronger cut.
    If no cycle is found we fall back to the previous behaviour.
    """

    # Build directed edges according to the ordering decisions
    adj = {}
    edge_lookup = {}
    for (t1, o1, t2, o2), val in orderings.items():
        if val not in (0, 1):
            # Skip fractional values; they should not occur with the current
            # master model but we guard against it.
            continue
        if val == 1:
            u, v = (t1, o1), (t2, o2)
        else:
            u, v = (t2, o2), (t1, o1)
        adj.setdefault(u, []).append(v)
        edge_lookup[(u, v)] = (t1, o1, t2, o2)

    # Depth-first search to detect any cycle in the directed graph.  As soon as
    # one cycle is found we stop and extract the corresponding ordering keys.
    stack = []
    on_path = set()
    visited = set()

    def dfs(node):
        visited.add(node)
        on_path.add(node)
        stack.append(node)
        for nxt in adj.get(node, []):
            if nxt not in visited:
                result = dfs(nxt)
                if result:
                    return result
            elif nxt in on_path:
                # Cycle found – extract from nxt back to current node
                cycle_nodes = stack[stack.index(nxt):] + [nxt]
                cycle_edges = []
                for a, b in zip(cycle_nodes, cycle_nodes[1:]):
                    key = edge_lookup.get((a, b))
                    if key is not None:
                        cycle_edges.append(key)
                return cycle_edges
        stack.pop()
        on_path.remove(node)
        return None

    cycle = None
    for node in list(adj):
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                break

    # If a cycle was detected we return exactly those edges, otherwise all
    # provided keys as a very weak fall-back cut.
    return cycle if cycle else list(orderings.keys())

def export_solution(x_vals, objective, output_path):
    events = [
        {"train": int(t), "operation": int(o), "time": int(round(t0))}
        for (t, o), t0 in x_vals.items()
    ]
    events.sort(key=lambda e: (e["time"], e["train"], e["operation"]))

    solution = {
        "objective_value": round(objective, 2),
        "events": events
    }

    with open(output_path, "w") as f:
        json.dump(solution, f, indent=2)

    print(f"✅ Lösung exportiert → {output_path}")

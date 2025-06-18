# cuts.py (ergänzt um JSON-Exportfunktion)
import json

def generate_cut(conflict):
    """
    Konflikt ist eine Liste von Konfliktpaaren, z. B. [(t1,o1,t2,o2), ...]
    Wir erzeugen einen Cut: x_{12} + x_{23} + ... <= len - 1
    """
    return conflict

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

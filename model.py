# model.py (mit Pfadgenerierung)
class Operation:
    def __init__(self, train_id, op_id, min_duration, resources=None, successors=None, start_lb=None, start_ub=None):
        self.train_id = train_id
        self.op_id = op_id
        self.min_duration = min_duration
        self.resources = resources or []
        self.successors = successors or []
        self.start_lb = start_lb
        self.start_ub = start_ub


class Train:
    def __init__(self, train_id, operations):
        self.train_id = train_id
        self.operations = operations  # Liste von Operationen

    def generate_paths(self):
        paths = []

        def dfs(current_path, visited):
            last_op = current_path[-1]
            if not self.operations[last_op].successors:
                paths.append(current_path[:])
                return
            for succ in self.operations[last_op].successors:
                if succ not in visited:
                    current_path.append(succ)
                    visited.add(succ)
                    dfs(current_path, visited)
                    current_path.pop()
                    visited.remove(succ)

        dfs([0], {0})
        return paths


class DisplibInstance:
    def __init__(self, trains, objectives):
        self.trains = trains  # Liste von Train-Objekten
        self.objectives = objectives

    def get_resource_usage(self):
        usage = {}
        for train in self.trains:
            for op in train.operations:
                for r in op.resources:
                    usage.setdefault(r["resource"], []).append((train.train_id, op.op_id))
        return usage

    def get_conflicts(self):
        usage = self.get_resource_usage()
        conflicts = set()
        for res, ops in usage.items():
            for i in range(len(ops)):
                for j in range(i+1, len(ops)):
                    conflicts.add((*ops[i], *ops[j]))
        return list(conflicts)

    def generate_paths_dict(self):
        return {str(train.train_id): train.generate_paths() for train in self.trains}

from typing import Dict, Tuple, List
from ortools.sat.python import cp_model

from custom_types import ModelVar, Curriculum

class SolverCallbackUtil(cp_model.CpSolverSolutionCallback):
    """ Solver callback containing methods that are useful for other callbacks.
    """

    def __init__(self,
                 model_vars: Dict[Tuple[str,
                                        int,
                                        str],
                                  ModelVar],
                 curricula: List[Curriculum],
                 n_days: int,
                 n_periods: int,
                 n_solutions: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._model_vars = model_vars
        self._curricula = curricula
        self._n_days = n_days
        self._n_periods = n_periods
        self._solutions = set(range(n_solutions))
        self._solution_count = 0
        self._objective = None

    def sol_to_str(self):
        out = []
        for d in range(self._n_days):
            out.append(f"\nDay {d}")
            for cur_id, cur in self._curricula.items():
                out.append(f"Curriculum {cur_id}")
                period_strs = [None] * self._n_periods
                for c_id in cur.courses.keys():
                    start = self.Value(self._model_vars[cur_id, d, c_id].start)
                    end = self.Value(self._model_vars[cur_id, d, c_id].end)
                    for idx in range(start, end):
                        assert not period_strs[idx]
                        period_strs[idx] = f"Period {idx}: course {c_id}"
                for idx in range(self._n_periods):
                    if not period_strs[idx]:
                        period_strs[idx] = f"Period {idx}: no course"
                    out.append(period_strs[idx])
        return "\n".join(out)

    def solution_count(self):
        return self._solution_count

    def set_objective(self, obj: ModelVar):
        self._objective = obj


class SchedPartialSolutionPrinter(SolverCallbackUtil):

    def __init__(self,
                 model_vars: Dict[Tuple[int,
                                        int],
                                  ModelVar],
                 curricula: Dict[str,
                                 Curriculum],
                 n_days: int,
                 n_periods: int,
                 n_solutions: int):
        SolverCallbackUtil.__init__(
            self, model_vars, curricula, n_days, n_periods, n_solutions)

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print(f'\nSolution {self._solution_count}')
            if self._objective:
                print(f'Objective: {self.Value(self._objective)}')
            else:
                print(f'Objective: {self.ObjectiveValue()}')
            print(self.sol_to_str())
        else:
            self.StopSearch()
        self._solution_count += 1


class SchedPartialSolutionSerializer(SolverCallbackUtil):

    def __init__(self,
                 model_vars: Dict[Tuple[str,
                                        int,
                                        str],
                                  ModelVar],
                 curricula: Dict[str,
                                 Curriculum],
                 n_days: int,
                 n_periods: int,
                 n_solutions: int):
        self.solutions = {"n_solutions": 0,
                          "solutions": []
                          }
        SolverCallbackUtil.__init__(
            self, model_vars, curricula, n_days, n_periods, n_solutions)

    def serialize_sol(self):
        solution = {'solution_id': str(self._solution_count),
                    'curricula': []}
        for cur_id, cur in self._curricula.items():
            new_curriculum = {'curriculum_id': cur_id,
                              'courses': []}
            solution['curricula'].append(new_curriculum)
            for c_id in cur.courses.keys():
                new_course = {'course_id': c_id,
                              'schedule': []}
                solution['curricula'][-1]['courses'].append(new_course)
                for d in range(self._n_days):
                    start = self.Value(self._model_vars[cur_id, d, c_id].start)
                    duration = self.Value(
                        self._model_vars[cur_id, d, c_id].duration)
                    if duration:
                        day_sched = {'day': d,
                                     'start': start,
                                     'duration': duration}
                        solution['curricula'][-1]['courses'][-1]['schedule'].append(
                            day_sched)
        self.solutions["solutions"].append(solution)
        self.solutions["n_solutions"] += 1

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            self.serialize_sol()
        else:
            self.StopSearch()
        self._solution_count += 1
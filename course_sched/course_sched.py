import collections
import os
from typing import List, Tuple, NewType, Dict
from dataclasses import dataclass
from ortools.sat.python import cp_model

from dotenv import load_dotenv
load_dotenv()

Interval = NewType('Interval', Tuple[int, int])


@dataclass
class ModelVar:
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar
    duration: cp_model.IntVar


class InvalidNumPeriods(Exception):
    pass


class DuplicateCourseId(Exception):
    pass


class ModelVarsNotInitialized(Exception):
    pass


class Course:

    def __init__(self, _id: str, n_periods: int):
        self._id = _id
        self.n_periods = n_periods
        self.curricula = {}
        if n_periods == 6:
            self.max_lecture_len = 6
        elif n_periods == 4:
            self.max_lecture_len = 2
        else:
            raise InvalidNumPeriods


class Curriculum:

    def __init__(self, _id: str, courses: List[Course]):
        self._id = _id
        self._verify_unique_ids(courses)
        self._add_courses(courses)

    def _verify_unique_ids(self, courses: List[Course]):
        ids = set()
        for course in courses:
            if course._id in ids:
                raise DuplicateCourseId
            ids.add(course._id)

    def _add_courses(self, courses: List[Course]):
        self.courses = {}  # mapping from course id to `Course`
        for course in courses:
            self.courses[course._id] = course


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


COURSE_GRANULARITY = [2, 3, 6]           # possible course lenghts in periods
MIN_COURSE_LEN = min(COURSE_GRANULARITY)  # minimum course length in periods
MAX_COURSE_LEN = max(COURSE_GRANULARITY)  # maximum course length in periods


class CourseSched:

    def __init__(self, n_days: int, n_periods: int,
                 curricula: List[Curriculum]):
        """ Initializes Course Scheduler.
            `n_days`: number of days per week
            `n_periods`: number of periods per day (1 period is a 30-min block)
            `model`: CP-SAT model
            `model_vars`: mapping from (`course_id`, `day`) tuple to `ModelVar` which contains:
                              * `start` model integer variable (IntVar)
                              * `end` model integer variable (IntVar)
                              * `duration` model integer variable (IntVar)
                              * `interval` model interval variable created from
                                the three integer variables above (IntervalVar)
            `day_to_intervals` - mapping from `day` to list of interval variables for that day.
        """
        self.n_days = n_days             # num of days per week
        self.n_periods = n_periods       # num 30-min periods per day
        self.model = cp_model.CpModel()
        self.model_vars = {}  # defined in _init_model_vars()
        self.cur_day_to_intervals = collections.defaultdict(list)
        self.course_to_curricula = collections.defaultdict(list)
        self.curricula = {}  # mapping from curriculum id to `Curriculum`
        self._init_model_vars(curricula)  # initializes model vars
        self.solver = None  # defined in solve()
        self.obj_int_vars = []
        self.obj_int_coeffs = []
        self.is_optimization = False  # optimize using soft constraints or search all feasible

    def _add_curricula(self, curricula: List[Curriculum]):
        """ Creates mapping from curricula ids to corresponding curricula.
        """
        for curriculum in curricula:
            self.curricula[curriculum._id] = curriculum
        self._init_course_to_curricula()

    def _init_course_to_curricula(self):
        """ Creates mapping from course id to list of curriculum ids.
            Course is part of those curricula.
        """
        for cur_id, cur in self.curricula.items():
            for c_id, c in cur.courses.items():
                self.course_to_curricula[c_id].append(cur_id)

    def _init_model_vars(self, curricula: List[Curriculum]):
        """ Initializes model variables and adds them to
            `model_vars` and `day_to_intervals`.

            This method has to be called before any constraint is added to the model.
        """
        self._add_curricula(curricula)
        for d in range(self.n_days):
            for cur_id, cur in self.curricula.items():
                for c_id, c in cur.courses.items():
                    suffix = f'_cur{cur_id}d{d}c{c_id}'
                    start_var = self.model.NewIntVar(
                        0, self.n_periods - MIN_COURSE_LEN, 'start' + suffix)
                    end_var = self.model.NewIntVar(0, self.n_periods,
                                                   'end' + suffix)
                    duration_var = self.model.NewIntVar(0, c.max_lecture_len,
                                                        'duration' + suffix)
                    interval_var = self.model.NewIntervalVar(
                        start_var, duration_var, end_var, 'interval' + suffix)
                    self.model_vars[cur_id, d, c_id] = ModelVar(start=start_var,
                                                                end=end_var,
                                                                interval=interval_var,
                                                                duration=duration_var)
                    self.cur_day_to_intervals[cur_id, d].append(interval_var)

    def add_no_overlap_constraints(self):
        """ Ensures that courses on the same day do not overlap.
        """
        for d in range(self.n_days):
            for cur_id in self.curricula.keys():
                self.model.AddNoOverlap(self.cur_day_to_intervals[cur_id, d])

    def add_sync_across_curricula_constraints(self):
        """ Ensures that courses shared across multiple curricula happen at the same time.

            E.g. a course is shared across multiple curricula; that is there
            are copies of interval variable for the same course in different.
            Let's say those interval variables are A, B and C (course is shared across
            3 curricula). The following must be true for each day of the week:

            # course doesn't happen on this day (conjunction A)
            (A.duration == 0 AND B.duration == 0 AND C.duration == 0)
            OR
            # course happens in the same interval in all curricula (conjunction B)
            (A.start == B.start AND A.end == B.end AND B.start == C.start AND B.end == C.end)
        """
        assert self.model_vars  # check that model variables are initialized
        prefix = 'sync_across_cur'
        for c_id, cur_ids in self.course_to_curricula.items():
            if len(cur_ids) > 1:
                for d in range(self.n_days):

                    conjunction_a = []
                    conjunction_a_bool = self.model.NewBoolVar(
                        prefix + f'_a_bool_d{d}c{c_id}')
                    for cur_id in cur_ids:
                        duration = self.model_vars[cur_id, d, c_id].duration
                        bool_a = self.model.NewBoolVar(
                            prefix + f'_a_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 0).OnlyEnforceIf(bool_a)
                        conjunction_a.append(bool_a)
                    self.model.AddBoolAnd(conjunction_a).OnlyEnforceIf(
                        conjunction_a_bool)

                    conjunction_b = []
                    conjunction_b_bool = self.model.NewBoolVar(
                        prefix + f'_b_bool_d{d}c{c_id}')
                    for prev_cur_id, next_cur_id in zip(
                            cur_ids[:-1], cur_ids[1:]):

                        prev_start = self.model_vars[prev_cur_id,
                                                     d, c_id].start
                        next_start = self.model_vars[next_cur_id,
                                                     d, c_id].start
                        bool_b_start = self.model.NewBoolVar(
                            prefix + f'_b_start_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(prev_start == next_start).OnlyEnforceIf(
                            bool_b_start)
                        conjunction_b.append(bool_b_start)

                        prev_end = self.model_vars[prev_cur_id, d, c_id].end
                        next_end = self.model_vars[next_cur_id, d, c_id].end
                        bool_b_end = self.model.NewBoolVar(
                            prefix + f'_b_end_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(
                            prev_end == next_end).OnlyEnforceIf(bool_b_end)
                        conjunction_b.append(bool_b_end)

                    self.model.AddBoolAnd(conjunction_b).OnlyEnforceIf(
                        conjunction_b_bool)

                    self.model.AddBoolOr(
                        [conjunction_a_bool, conjunction_b_bool])

    def add_course_len_constraints(self):
        """ Ensures that each course happens exactly `course.n_periods` periods per week.
        """
        for cur_id, cur in self.curricula.items():
            for c_id, c in cur.courses.items():
                self.model.Add(sum(self.model_vars[cur_id, d, c_id].duration for d in
                                   range(self.n_days)) == c.n_periods)

    def add_unavailability_constraints(
            self, c_id: str, day: int, intervals: List[Interval]):
        """ Marks certain `intervals` of a particular `day` unavailable for scheduling for a
            particular course (identified by `c_id`).
        """
        assert c_id in self.course_to_curricula  # check that course id exists
        interval_vars = []
        for interval in intervals:
            assert len(interval) == 2
            start, end = interval
            suffix = f'_d{day}c{c_id}interval-{start}_{end}'
            interval_var = self.model.NewIntervalVar(
                start, end - start, end, 'unavail_interval' + suffix)
            interval_vars.append(interval_var)

        for cur_id in self.course_to_curricula[c_id]:
            interval_vars.append(self.model_vars[cur_id, day, c_id].interval)

        self.model.AddNoOverlap(interval_vars)

    def add_lecture_len_constraints(self):
        """ Ensures that each course takes up consecutive number of periods per day:
              * If a course has 6 periods per week, it can take up 2, 3, 6 periods.
              * If a course has 4 periods per week, it can take up 2 periods only.
        """
        for cur_id, cur in self.curricula.items():
            for d in range(self.n_days):
                for c_id, c in cur.courses.items():

                    lecture_constraint_disjunction = []

                    # Case when course doesn't take place on this day at all
                    no_periods = self.model.NewBoolVar(
                        f'0_periods_cur{cur_id}d{d}c{c_id}')
                    duration = self.model_vars[cur_id, d, c_id].duration
                    self.model.Add(duration == 0).OnlyEnforceIf(no_periods)
                    lecture_constraint_disjunction.append(no_periods)

                    two_periods = self.model.NewBoolVar(
                        f'2_periods_cur{cur_id}d{d}c{c_id}')
                    self.model.Add(duration == 2).OnlyEnforceIf(two_periods)
                    lecture_constraint_disjunction.append(two_periods)

                    if c.max_lecture_len == 6:
                        three_periods = self.model.NewBoolVar(
                            f'3_periods_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 3).OnlyEnforceIf(
                            three_periods)
                        lecture_constraint_disjunction.append(three_periods)

                        six_periods = self.model.NewBoolVar(
                            f'6_periods_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 6).OnlyEnforceIf(
                            six_periods)
                        lecture_constraint_disjunction.append(six_periods)

                    self.model.AddBoolOr(lecture_constraint_disjunction)

    def add_lecture_symmetry_constraints(self):
        """ Ensures that lectures scheduled on Tuesday are scheduled at the
            same time on Thursday.

            For each course C, the following is true:

            C has one 3-hour lecture
            XOR # conjunction A
            (C lecture on Tue starts at the same time as lecture on Thu AND
             C lecture duration on Tue is the same as on Thu AND
             C lecture duration on Tue is not zero) (1 or 2 hour duration is possible)
            XOR # conjunction B
            (C lecture on Mon starts at the same time as on Wed AND
             C lecture duration on Mon is the same as on Wed AND
             C lecture on Wed starts at the same time as on Fri AND
             C lecture duration on Wed is the same as on Fri AND
             C lecture duration on Mon is not zero) (only 1 hour duration possible here)
            XOR # conjunction C
            (C lecture on Mon starts at the same time as lecture on Wed AND
             C lecture duration on Mon is the same as on Wed AND
             C lecture duration on Fri is zero AND
             C lecture duration on Mon is nonzero)

        """
        # TODO: can courses with two lectures a week happen on Mon, Fri or Wed,
        # Fri

        assert self.n_days == 5
        for c_id, cur_ids in self.course_to_curricula.items():
            for cur_id in cur_ids:

                mon_duration = self.model_vars[cur_id, 0, c_id].duration
                tue_duration = self.model_vars[cur_id, 1, c_id].duration
                wed_duration = self.model_vars[cur_id, 2, c_id].duration
                thu_duration = self.model_vars[cur_id, 3, c_id].duration
                fri_duration = self.model_vars[cur_id, 4, c_id].duration
                mon_start = self.model_vars[cur_id, 0, c_id].start
                tue_start = self.model_vars[cur_id, 1, c_id].start
                wed_start = self.model_vars[cur_id, 2, c_id].start
                thu_start = self.model_vars[cur_id, 3, c_id].start
                fri_start = self.model_vars[cur_id, 4, c_id].start

                prefix = 'lecture_symm'

                # C has one 3-hour lecture
                mon_lec = self.model.NewBoolVar(
                    prefix + f'_mon_lec_cur{cur_id}c{c_id}')
                self.model.Add(mon_duration == 6).OnlyEnforceIf(mon_lec)
                tue_lec = self.model.NewBoolVar(
                    prefix + f'_tue_lec_cur{cur_id}c{c_id}')
                self.model.Add(tue_duration == 6).OnlyEnforceIf(tue_lec)
                wed_lec = self.model.NewBoolVar(
                    prefix + f'_wed_lec_cur{cur_id}c{c_id}')
                self.model.Add(wed_duration == 6).OnlyEnforceIf(wed_lec)
                thu_lec = self.model.NewBoolVar(
                    prefix + f'_thu_lec_cur{cur_id}c{c_id}')
                self.model.Add(thu_duration == 6).OnlyEnforceIf(thu_lec)
                fri_lec = self.model.NewBoolVar(
                    prefix + f'_fri_lec_cur{cur_id}c{c_id}')
                self.model.Add(fri_duration == 6).OnlyEnforceIf(fri_lec)

                # Conjunction A
                tue_thu_start = self.model.NewBoolVar(
                    prefix + f'_tue_thu_start{cur_id}c{c_id}')
                self.model.Add(tue_start == thu_start).OnlyEnforceIf(
                    tue_thu_start)
                tue_thu_duration = self.model.NewBoolVar(
                    prefix + f'_tue_thu_duration{cur_id}c{c_id}')
                self.model.Add(tue_duration == thu_duration).OnlyEnforceIf(
                    tue_thu_duration)
                tue_nonzero_duration = self.model.NewBoolVar(
                    prefix + f'_tue_nonzero_duration{cur_id}c{c_id}')
                self.model.Add(tue_duration != 0).OnlyEnforceIf(
                    tue_nonzero_duration)
                conjunction_a = self.model.NewBoolVar(
                    prefix + f'_conjunction_a_{cur_id}c{c_id}')
                self.model.AddBoolAnd([tue_thu_start,
                                       tue_thu_duration,
                                       tue_nonzero_duration]).OnlyEnforceIf(conjunction_a)

                # Conjunction B
                mon_wed_start = self.model.NewBoolVar(
                    prefix + f'_mon_wed_start{cur_id}c{c_id}')
                self.model.Add(mon_start == wed_start).OnlyEnforceIf(
                    mon_wed_start)
                mon_wed_duration = self.model.NewBoolVar(
                    prefix + f'_mon_wed_duration{cur_id}c{c_id}')
                self.model.Add(mon_duration == wed_duration).OnlyEnforceIf(
                    mon_wed_duration)
                wed_fri_start = self.model.NewBoolVar(
                    prefix + f'_wed_fri_start{cur_id}c{c_id}')
                self.model.Add(wed_start == fri_start).OnlyEnforceIf(
                    wed_fri_start)
                wed_fri_duration = self.model.NewBoolVar(
                    prefix + f'_wed_fri_duration{cur_id}c{c_id}')
                self.model.Add(wed_duration == fri_duration).OnlyEnforceIf(
                    wed_fri_duration)
                mon_nonzero_duration = self.model.NewBoolVar(
                    prefix + f'_mon_nonzero_duration{cur_id}c{c_id}')
                self.model.Add(mon_duration != 0).OnlyEnforceIf(
                    mon_nonzero_duration)
                conjunction_b = self.model.NewBoolVar(
                    prefix + f'_conjunction_b_{cur_id}c{c_id}')
                self.model.AddBoolAnd([mon_wed_start,
                                       mon_wed_duration,
                                       wed_fri_start,
                                       wed_fri_duration,
                                       mon_nonzero_duration]).OnlyEnforceIf(conjunction_b)

                # Conjunction C
                fri_zero_duration = self.model.NewBoolVar(
                    prefix + f'_fri_zero_duration{cur_id}c{c_id}')
                self.model.Add(fri_duration == 0).OnlyEnforceIf(
                    fri_zero_duration)
                conjunction_c = self.model.NewBoolVar(
                    prefix + f'_conjunction_c_{cur_id}c{c_id}')
                self.model.AddBoolAnd([mon_wed_start,
                                       mon_wed_duration,
                                       fri_zero_duration,
                                       mon_nonzero_duration]).OnlyEnforceIf(conjunction_c)
                # XOR
                self.model.AddBoolXOr([mon_lec,
                                       tue_lec,
                                       wed_lec,
                                       thu_lec,
                                       fri_lec,
                                       conjunction_a,
                                       conjunction_b,
                                       conjunction_c])

    def add_soft_start_time_constraints(self, soft_min: int,
                                        soft_max: int,
                                        max_cost: int,
                                        min_cost: int):
        """ Add soft constraints on how early the first class of the day takes place and
            how late the last class finishes.

            Create delta variables (diff between class start and soft constrain value)
            and their coefficients.
        """
        assert min_cost >= 0 and min_cost < self.n_periods
        assert max_cost >= 0 and max_cost < self.n_periods

        self.is_optimization = True

        prefix = 'soft_start_end'

        for d in range(self.n_days):
            for cur_id, cur in self.curricula.items():
                for c_id, c in cur.courses.items():

                    # penalize lectures that start too early
                    delta = self.model.NewIntVar(-self.n_periods,
                                                 self.n_periods, '')
                    start = self.model_vars[cur_id, d, c_id].start
                    # delta is positive when lecture start time is < soft min
                    self.model.Add(delta == soft_min - start)
                    excess = self.model.NewIntVar(
                        0, self.n_periods, prefix + '_under_sum')
                    self.model.AddMaxEquality(excess, [delta, 0])
                    self.obj_int_vars.append(excess)
                    self.obj_int_coeffs.append(min_cost)

                    # penalize lectures that start too late
                    delta = self.model.NewIntVar(-self.n_periods,
                                                 self.n_periods, '')
                    # delta is positive when lecture start time is > soft max
                    self.model.Add(delta == start - soft_max)
                    excess = self.model.NewIntVar(
                        0, self.n_periods, prefix + '_over_sum')
                    self.model.AddMaxEquality(excess, [delta, 0])
                    self.obj_int_vars.append(excess)
                    self.obj_int_coeffs.append(max_cost)

    def _set_objective(self):
        """ Set objective of the model to minimize the sum of cost vars multiplied by
            cost coefficients.
        """
        assert self.obj_int_vars and self.obj_int_coeffs
        assert self.is_optimization
        self.model.Minimize(
            sum(self.obj_int_vars[i] * self.obj_int_coeffs[i]
                for i in range(len(self.obj_int_vars))))

    def solve(self, callback: cp_model.CpSolverSolutionCallback,
              max_time: int = None):
        """ Create CP model solver and search for solutions for the model.
            `callback`: a class implementing `cp_model.CpSolverSolutionCallback`
            `max_time`: solution search timeout in seconds
        """
        self.solver = cp_model.CpSolver()
        self.solver.parameters.linearization_level = 0
        if max_time:
            self.solver.parameters.max_time_in_seconds = max_time
        if self.is_optimization:
            self.solver.parameters.num_search_workers = 8
            self._set_objective()
            self.solver.SolveWithSolutionCallback(self.model, callback)
        else:
            self.solver.SearchForAllSolutions(self.model, callback)

    def print_statistics(self, callback: cp_model.CpSolverSolutionCallback):
        """ Print solution statistics.
        """
        assert self.solver
        print()
        print('Statistics')
        print(f'Optimal solution: {self.solver.ResponseStats()}')


def main():

    n_periods = 26  # real day has os.getenv("PERIODS_PER_DAY") periods
    n_days = int(os.environ.get("DAYS_PER_WEEK", 5))

    c1 = Course("0UoeRGKWlpKzZgs7", 6)
    c2 = Course("FQJSAdpeIy9rJU1H", 6)
    c3 = Course("8sMA05cToLsEKB3y", 4)
    c4 = Course("BbjRKtortAflVFLL", 6)
    courses0 = [c1, c2, c3, c4]

    c5 = Course("hFUhTu8WIEeQEQ3i", 4)
    c6 = Course("YlFH40I1LBgH9vEI", 6)
    c7 = Course("jWtVT6TsTjz0lFQb", 6)
    courses1 = [c4, c5, c6, c7]

    cur0 = Curriculum("hXkY1ChCPUcdRMbz", courses0)
    cur1 = Curriculum("yGGLYSENM97GC0A3", courses1)
    curricula = [cur0, cur1]

    sched = CourseSched(n_days, n_periods, curricula)
    sched.add_no_overlap_constraints()
    sched.add_course_len_constraints()
    sched.add_lecture_len_constraints()
    sched.add_sync_across_curricula_constraints()
    sched.add_lecture_symmetry_constraints()

    sched.add_unavailability_constraints(
        "hFUhTu8WIEeQEQ3i", 2, [(0, 4), (6, 9)])
    sched.add_unavailability_constraints("hFUhTu8WIEeQEQ3i", 4, [(4, 9)])
    sched.add_unavailability_constraints(
        "jWtVT6TsTjz0lFQb", 3, [(10, 14), (16, 19)])

    # penalize classes that start earlier than 10:30 (4) or later than 17:00 (17)
    # penalize early classes twice as much as late ones
    sched.add_soft_start_time_constraints(4, 17, 2, 1)

    n_solutions = 1000  # this is ignored for optimization problems

    solution_printer = SchedPartialSolutionPrinter(sched.model_vars,
                                                   sched.curricula,
                                                   sched.n_days,
                                                   sched.n_periods,
                                                   n_solutions)
    sched.solve(solution_printer)
    sched.print_statistics(solution_printer)


if __name__ == '__main__':
    main()

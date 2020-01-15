from ortools.sat.python import cp_model
import collections
from typing import List, Tuple, NewType, Dict
from dataclasses import dataclass

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

    def __init__(self, _id, n_periods):
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

    def __init__(self, _id: int, courses: List[Course]):
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
        self.courses = {} # mapping from course id to `Course`
        for course in courses:
            self.courses[course._id] = course


class SolverCallbackUtil(cp_model.CpSolverSolutionCallback):
    """ Solver callback containing methods that are useful for other callbacks.
    """

    def __init__(self, model_vars: Dict[Tuple[int, int], ModelVar], curricula: List[Curriculum], 
                 n_days: int, n_periods: int, n_solutions: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._model_vars = model_vars
        self._curricula = curricula 
        self._n_days = n_days
        self._n_periods = n_periods
        self._solutions = set(range(n_solutions))
        self._solution_count = 0


    def sol_to_str(self):
        out = ["\n"]
        for d in range(self._n_days):
            out.append(f"Day {d}")
            for cur_id, cur in self._curricula.items():
                out.append(f"Curriculum {cur_id}")
                period_strs = [None] * self._n_periods
                for c_id in cur.courses.keys():
                    start = self.Value(self._model_vars[cur_id, d, c_id].start)
                    end = self.Value(self._model_vars[cur_id, d, c_id].end)
                    for idx in range(start, end):
                        assert(not period_strs[idx])
                        period_strs[idx] = f"Period {idx}: course {c_id}"
                for idx in range(self._n_periods):
                    if not period_strs[idx]:
                        period_strs[idx] = f"Period {idx}: no course"
                    out.append(period_strs[idx])
        return "\n".join(out)

    def solution_count(self):
        return self._solution_count

class SchedPartialSolutionPrinter(SolverCallbackUtil):

    def __init__(self, model_vars: Dict[Tuple[int, int], ModelVar], 
            curricula: Dict[int, Curriculum], n_days: int, n_periods: int, n_solutions: int):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print(f'Solution {self._solution_count}')
            print(self.sol_to_str())
        else:
            self.StopSearch()
        self._solution_count += 1


COURSE_GRANULARITY = [2, 3, 6]           # possible course lenghts in periods
MIN_COURSE_LEN = min(COURSE_GRANULARITY) # minimum course length in periods
MAX_COURSE_LEN = max(COURSE_GRANULARITY) # maximum course length in periods


class CourseSched:

    def __init__(self, n_days: int, n_periods: int, curricula: List[Curriculum]):
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
        self.model_vars = {}           
        self.cur_day_to_intervals = collections.defaultdict(list)
        self.course_to_curricula = collections.defaultdict(list)
        self._init_model_vars(curricula) # initializes model vars

    def _add_curricula(self, curricula: List[Curriculum]):
        """ Creates mapping from curricula ids to corresponding curricula.
        """
        self.curricula = {} # mapping from curriculum id to `Curriculum`
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
                    suffix =  f'_cur{cur_id}d{d}c{c_id}'
                    start_var = self.model.NewIntVar(0, self.n_periods - MIN_COURSE_LEN,
                                                     'start' + suffix)
                    end_var = self.model.NewIntVar(0, self.n_periods,
                                                   'end' + suffix)
                    duration_var = self.model.NewIntVar(0, c.max_lecture_len,
                                                        'duration' + suffix)
                    interval_var = self.model.NewIntervalVar(start_var, duration_var,
                                                             end_var, 'interval' + suffix)
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
        assert(self.model_vars) # check that model variables are initialized
        prefix = 'sync_across_cur'
        for c_id, cur_ids in self.course_to_curricula.items():
            if len(cur_ids) > 1:
                for d in range(self.n_days):

                    conjunction_a = []
                    conjunction_a_bool = self.model.NewBoolVar(prefix + 
                            f'_a_bool_d{d}c{c_id}')
                    for cur_id in cur_ids:
                        duration = self.model_vars[cur_id, d, c_id].duration
                        bool_a = self.model.NewBoolVar(prefix + 
                                f'_a_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 0).OnlyEnforceIf(bool_a)
                        conjunction_a.append(bool_a)
                    self.model.AddBoolAnd(conjunction_a).OnlyEnforceIf(conjunction_a_bool)

                    conjunction_b = []
                    conjunction_b_bool = self.model.NewBoolVar(prefix + 
                            f'_b_bool_d{d}c{c_id}')
                    for prev_cur_id, next_cur_id in zip(cur_ids[:-1], cur_ids[1:]):
                        
                        prev_start = self.model_vars[prev_cur_id, d, c_id].start
                        next_start = self.model_vars[next_cur_id, d, c_id].start
                        bool_b_start = self.model.NewBoolVar(prefix + 
                                f'_b_start_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(prev_start == next_start).OnlyEnforceIf(bool_b_start)
                        conjunction_b.append(bool_b_start)

                        prev_end = self.model_vars[prev_cur_id, d, c_id].end
                        next_end= self.model_vars[next_cur_id, d, c_id].end
                        bool_b_end = self.model.NewBoolVar(prefix + 
                                f'_b_end_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(prev_end == next_end).OnlyEnforceIf(bool_b_end)
                        conjunction_b.append(bool_b_end)

                    self.model.AddBoolAnd(conjunction_b).OnlyEnforceIf(conjunction_b_bool)

                    self.model.AddBoolOr([conjunction_a_bool, conjunction_b_bool])

    def add_course_len_constraints(self):
        """ Ensures that each course happens exactly `course.n_periods` periods per week.
        """
        for cur_id, cur in self.curricula.items():
            for c_id, c in cur.courses.items():
                self.model.Add(sum(self.model_vars[cur_id, d, c_id].duration for d in \
                                   range(self.n_days)) == c.n_periods)

    def add_unavailability_constraints(self, c_id: int, day: int, intervals: List[Interval]):
        """ Marks certain `intervals` of a particular `day` unavailable for scheduling for a
            particular course (identified by `c_id`).
        """
        assert(c_id in self.course_to_curricula) # check that course id exists
        interval_vars = []
        for interval in intervals:
            assert(len(interval) == 2)
            start, end = interval
            suffix = f'_d{day}c{c_id}interval-{start}_{end}'
            interval_var = self.model.NewIntervalVar(start, end - start, 
                                                     end, 'unavail_interval' + suffix)
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
                    no_periods = self.model.NewBoolVar(f'0_periods_cur{cur_id}d{d}c{c_id}')
                    duration = self.model_vars[cur_id, d, c_id].duration
                    self.model.Add(duration == 0).OnlyEnforceIf(no_periods)
                    lecture_constraint_disjunction.append(no_periods)

                    two_periods = self.model.NewBoolVar(f'2_periods_cur{cur_id}d{d}c{c_id}')
                    self.model.Add(duration == 2).OnlyEnforceIf(two_periods)
                    lecture_constraint_disjunction.append(two_periods)

                    if c.max_lecture_len == 6:
                        three_periods = self.model.NewBoolVar(f'3_periods_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 3).OnlyEnforceIf(three_periods)
                        lecture_constraint_disjunction.append(three_periods)

                        six_periods = self.model.NewBoolVar(f'6_periods_cur{cur_id}d{d}c{c_id}')
                        self.model.Add(duration == 6).OnlyEnforceIf(six_periods)
                        lecture_constraint_disjunction.append(six_periods)

                    self.model.AddBoolOr(lecture_constraint_disjunction)

    def add_lecture_symmetry_constraints(self):
        """ Ensures that lectures scheduled on Tuesday are scheduled at the
            same time on Thursday. 

            For each course C, the following is true:

            (C doesn't take place on Tue AND 
             C doesn't take place on Thu)
            XOR
            C takes place on Tue only (3 hour lecture)
            XOR
            C takes place on Thu only (3 hour lecture)
            XOR
            (C starts at the same time on Tue as on Thu AND
             C duration on Tue is the same as on Thu)



        """
        assert(self.n_days == 5)
        for c_id, cur_ids in self.course_to_curricula.items():
            for cur_id in cur_ids:

                # Courses scheduled for Tuesday and Thursday
                tue_duration = self.model_vars[cur_id, 1, c_id].duration
                thu_duration = self.model_vars[cur_id, 3, c_id].duration

                no_course_tue = self.model.NewBoolVar(f'no_course_tue_cur{cur_id}c{c_id}')
                self.model.Add(tue_duration == 0).OnlyEnforceIf(no_course_tue)
                no_course_thu = self.model.NewBoolVar(f'no_course_thu_cur{cur_id}c{c_id}')
                self.model.Add(thu_duration == 0).OnlyEnforceIf(no_course_thu)
                no_course_tue_thu = self.model.NewBoolVar(f'no_course_tue_thu_cur{cur_id}c{c_id}')
                self.model.AddBoolAnd([no_course_tue, 
                                       no_course_thu]).OnlyEnforceIf(no_course_tue_thu)

                course_tue_only = self.model.NewBoolVar(f'course_tue_only_cur{cur_id}c{c_id}')
                self.model.Add(tue_duration == 6).OnlyEnforceIf(course_tue_only)

                course_thu_only = self.model.NewBoolVar(f'course_thu_only_cur{cur_id}c{c_id}')
                self.model.Add(thu_duration == 6).OnlyEnforceIf(course_thu_only)

                course_tue_thu_conjunction = self.model.NewBoolVar(f'course_tue_thu_conj_cur{cur_id}c{c_id}')
                course_tue_thu_start = self.model.NewBoolVar(f'course_tue_thu_start_cur{cur_id}c{c_id}')
                tue_start = self.model_vars[cur_id, 1, c_id].start
                thu_start = self.model_vars[cur_id, 3, c_id].start
                self.model.Add(tue_start == thu_start).OnlyEnforceIf(course_tue_thu_start)
                course_tue_thu_duration = self.model.NewBoolVar(f'course_tue_thu_duration_cur{cur_id}c{c_id}')
                self.model.Add(tue_duration == thu_duration).OnlyEnforceIf(course_tue_thu_duration)
                self.model.AddBoolAnd([course_tue_thu_start,
                                       course_tue_thu_duration]).OnlyEnforceIf(course_tue_thu_conjunction)

                self.model.AddBoolXOr([no_course_tue_thu, 
                                       course_tue_only,
                                       course_thu_only,
                                       course_tue_thu_conjunction])


    def solve(self, callback: cp_model.CpSolverSolutionCallback, max_time: int=None):
        """ Create CP model solver and search for solutions for the model.
            `callback`: a class implementing `cp_model.CpSolverSolutionCallback`
            `max_time`: solution search timeout in seconds
        """
        self.solver = cp_model.CpSolver()
        if max_time:
            self.solver.parameters.max_time_in_seconds = max_time
        self.solver.parameters.linearization_level = 0

        self.solver.SearchForAllSolutions(self.model, callback)


    def print_statistics(self, callback: cp_model.CpSolverSolutionCallback):
        """ Print solution statistics.
        """
        assert(self.solver)
        print('Statistics')
        print(f'  - conflicts       : {self.solver.NumConflicts()}')
        print(f'  - branches        : {self.solver.NumBranches()}')
        print(f'  - wall time       : {self.solver.WallTime()} s')
        print(f'  - solutions found : {callback.solution_count()}')


def main():

    n_periods = 8 # 26 8:30 = 0 -> 21:30 = 2 
    n_days = 5 

    c0 = Course(0, 6)
    c1 = Course(1, 4)
    c2 = Course(2, 6)
    c3 = Course(3, 6)

    c4 = Course(4, 6)
    c5 = Course(5, 6)
    c6 = Course(6, 6)

    courses0 = [c0, c1, c2, c3]
    courses1 = [c4, c3, c2, c1]

    cur0 = Curriculum(0, courses0)
    cur1 = Curriculum(1, courses1)
    curricula = [cur0, cur1]

    sched = CourseSched(n_days, n_periods, curricula)
    sched.add_no_overlap_constraints()
    sched.add_course_len_constraints()
    sched.add_lecture_len_constraints()
    sched.add_sync_across_curricula_constraints()
    sched.add_lecture_symmetry_constraints()

    sched.add_unavailability_constraints(0, 1, [(3, 5)])
    sched.add_unavailability_constraints(1, 1, [(3, 5)])
    sched.add_unavailability_constraints(2, 1, [(3, 5)])
    sched.add_unavailability_constraints(3, 1, [(3, 5)])
    sched.add_unavailability_constraints(4, 1, [(3, 5)])

    sched.add_unavailability_constraints(0, 3, [(3, 5)])
    sched.add_unavailability_constraints(1, 3, [(3, 5)])
    sched.add_unavailability_constraints(2, 3, [(3, 5)])
    sched.add_unavailability_constraints(3, 3, [(3, 5)])
    sched.add_unavailability_constraints(4, 3, [(3, 5)])
    # sched.add_unavailability_constraints(3, 1, [(0, 7)])
    # sched.add_unavailability_constraints(1, 0, [(0, 7)])
    # sched.add_unavailability_constraints(1, 1, [(2, 7)])
    # sched.add_unavailability_constraints(1, 2, [(2, 7)])

    n_solutions = 2999

    solution_printer = SchedPartialSolutionPrinter(sched.model_vars, 
                                                   sched.curricula, 
                                                   sched.n_days, 
                                                   sched.n_periods,
                                                   n_solutions)
    sched.solve(solution_printer)
    sched.print_statistics(solution_printer)

if __name__ == '__main__':
    main()

from ortools.sat.python import cp_model
import collections
from typing import List, Tuple, NewType, Dict
from dataclasses import dataclass

Interval = NewType('Interval', Tuple[int, int])

@dataclass
class CourseVar:
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar
    duration: cp_model.IntVar


class InvalidNumPeriods(Exception):
    pass


class Course:

    def __init__(self, _id, n_periods): # TODO: , curricula):
        self._id = _id
        self.n_periods = n_periods
        #self.curricula = curricula # list of curriculum ids
        if n_periods == 6:
            self.max_lecture_len = 6
        elif n_periods == 4:
            self.max_lecture_len = 2
        else:
            raise InvalidNumPeriods


class SolverCallbackUtil(cp_model.CpSolverSolutionCallback):
    """ Solver callback containing methods that are useful for other callbacks.
    """

    def __init__(self, course_vars: Dict[Tuple[int, int], CourseVar], courses: Dict[int, Course], 
                 n_days: int, n_periods: int, n_solutions: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._course_vars = course_vars
        self._courses = courses
        self._n_days = n_days
        self._n_periods = n_periods
        self._solutions = set(range(n_solutions))
        self._solution_count = 0

    def sol_to_str(self):
        out = ["\n"]
        for d in range(self._n_days):
            period_strs = [None] * self._n_periods
            out.append(f"Day {d}")
            for c_id in self._courses.keys():
                start = self.Value(self._course_vars[c_id, d].start)
                end = self.Value(self._course_vars[c_id, d].end)
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

    def __init__(self, course_vars: Dict[Tuple[int, int], CourseVar], courses: Dict[int, Course], 
                 n_days: int, n_periods: int, n_solutions: int):
        SolverCallbackUtil.__init__(self, course_vars, courses, n_days, n_periods, n_solutions)

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

    def __init__(self, n_days: int, n_periods: int):
        """ Initializes Course Scheduler.
            `n_days`: number of days per week
            `n_periods`: number of periods per day (1 period is a 30-min block)
            `model`: CP-SAT model
            `course_vars`: mapping from (`course_id`, `day`) tuple to `CourseVar` which contains:
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
        self.course_vars = {}           
        self.day_to_intervals = collections.defaultdict(list)

    def _add_courses(self, courses: List[Course]):
        self.courses = {} # mapping from course id to `Course`
        for course in courses:
            self.courses[course._id] = course

    def create_course_vars(self, courses: List[Course]):
        """ Initializes model variables and adds them to
            `course_vars` and `day_to_intervals`.

            This method has to be called before any constraint is added to the model.
        """
        self._add_courses(courses)
        for d in range(self.n_days):
            for c_id, c in self.courses.items():
                suffix =  f'_c{c_id}d{d}'
                start_var = self.model.NewIntVar(0, self.n_periods - MIN_COURSE_LEN, 'start' + suffix)
                end_var = self.model.NewIntVar(0, self.n_periods, 'end' + suffix)
                duration_var = self.model.NewIntVar(0, c.max_lecture_len, 'duration' + suffix)
                interval_var = self.model.NewIntervalVar(start_var, duration_var,
                                                         end_var, 'interval' + suffix)
                # TODO add curricula
                self.course_vars[c_id, d] = CourseVar(start=start_var, 
                                                      end=end_var, 
                                                      interval=interval_var,
                                                      duration=duration_var)
                self.day_to_intervals[d].append(interval_var)

    
    def add_no_overlap_constraints(self):
        """ Ensures that courses on the same day do not overlap.
        """
        assert(self.day_to_intervals) # check that model variables are initialized
        for d in range(self.n_days):
            self.model.AddNoOverlap(self.day_to_intervals[d])

    def add_course_len_constraints(self):
        """ Ensures that each course happens exactly `course.n_periods` periods per week.
        """
        assert(self.course_vars) # check that model variables are initialized
        for c_id, c in self.courses.items():
            self.model.Add(sum(self.course_vars[c_id, d].duration for d in range(self.n_days)) == c.n_periods)

    def add_unavailability_constraints(self, c_id: int, day: int, intervals: List[Interval]):
        """ Marks certain `intervals` of a particular `day` unavailable for scheduling for a
            particular course (identified by `c_id`).
        """
        assert(self.course_vars) # check that model variables are initialized
        assert(c_id in self.courses) # check that course id exists
        interval_vars = []
        for interval in intervals:
            assert(len(interval) == 2)
            start, end = interval
            suffix = f'_c{c_id}d{day}interval-{start}_{end}'
            interval_var = self.model.NewIntervalVar(start, end - start, 
                                                     end, 'unavail_interval' + suffix)
            interval_vars.append(interval_var)
        interval_vars.append(self.course_vars[c_id, day].interval)
        self.model.AddNoOverlap(interval_vars)


    def add_lecture_len_constraints(self):
        """ Ensures that each course takes up consecutive number of periods per day:
              * If a course has 6 periods per week, it can take up 2, 3, 6 periods.
              * If a course has 4 periods per week, it can take up 2 periods only.
        """
        assert(self.course_vars) # check that model variables are initialized
        for d in range(self.n_days):
            for c_id, c in self.courses.items():
                lecture_constraint_disjunction = []
                
                # Case when course doesn't take place on this day at all
                no_periods = self.model.NewBoolVar(f'no_periods_c{c_id}d{d}')
                self.model.Add(self.course_vars[c_id, d].duration == 0).OnlyEnforceIf(no_periods)
                lecture_constraint_disjunction.append(no_periods)

                two_periods = self.model.NewBoolVar(f'two_periods_c{c_id}d{d}')
                self.model.Add(self.course_vars[c_id, d].duration == 2).OnlyEnforceIf(two_periods)
                lecture_constraint_disjunction.append(two_periods)

                if c.max_lecture_len == 6:
                    three_periods = self.model.NewBoolVar(f'three_periods_c{c_id}d{d}')
                    self.model.Add(self.course_vars[c_id, d].duration == 3).OnlyEnforceIf(three_periods)
                    lecture_constraint_disjunction.append(three_periods)

                    six_periods = self.model.NewBoolVar(f'six_periods_c{c_id}d{d}')
                    self.model.Add(self.course_vars[c_id, d].duration == 6).OnlyEnforceIf(six_periods)
                    lecture_constraint_disjunction.append(six_periods)

                self.model.AddBoolOr(lecture_constraint_disjunction)

    def solve(self, callback: cp_model.CpSolverSolutionCallback, max_time: int=None):
        """ Create CP model solver and search for solutions for the model.
            `callback`: a class implementing `cp_model.CpSolverSolutionCallback`
            `max_time`: solution search timeout in seconds
        """
        assert(self.course_vars) # check that model variables are initialized
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
    # check: variable period
    # unavailability constraint (professor, admin)
    # classes operating over certain times

    n_periods = 8 # 26 8:30 = 0 -> 21:30 = 2 
    n_days = 3 

    c0 = Course(0, 6)
    c1 = Course(1, 4)
    c2 = Course(2, 6)
    c3 = Course(3, 6)

    courses = [c0, c1, c2, c3]

    sched = CourseSched(n_days, n_periods)
    sched.create_course_vars(courses)
    sched.add_no_overlap_constraints()
    sched.add_course_len_constraints()
    sched.add_unavailability_constraints(3, 0, [(0, 7)])
    sched.add_unavailability_constraints(3, 1, [(0, 7)])
    sched.add_unavailability_constraints(1, 0, [(0, 7)])
    sched.add_unavailability_constraints(1, 1, [(2, 7)])
    sched.add_unavailability_constraints(1, 2, [(2, 7)])
    sched.add_lecture_len_constraints()

    n_solutions = 100

    solution_printer = SchedPartialSolutionPrinter(sched.course_vars, 
                                                   sched.courses, 
                                                   sched.n_days, 
                                                   sched.n_periods,
                                                   n_solutions)
    sched.solve(solution_printer)
    sched.print_statistics(solution_printer)

if __name__ == '__main__':
    main()

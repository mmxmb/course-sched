import unittest
from ortools.sat.python import cp_model
from course_sched import CourseSched, Course, CourseVar, SolverCallbackUtil, COURSE_GRANULARITY

class TestSchedPeriodSumCallback(SolverCallbackUtil):

    def __init__(self, course_vars, courses, n_days, n_periods, n_solutions, expected):
        SolverCallbackUtil.__init__(self, course_vars, courses, n_days, n_periods, n_solutions)
        self.expected = expected
        self.actual = None

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            self.actual = {} 
            for c_id in self._courses.keys():
                self.actual[c_id] = 0
                for d in range(self._n_days):
                    duration = self.Value(self._course_vars[c_id, d].duration)
                    self.actual[c_id] += duration
            if self.actual != self.expected:
                self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1


class TestSchedUnavailabilityConstraintsCallback(SolverCallbackUtil):

    def __init__(self, course_vars, courses, n_days, n_periods, n_solutions):
        SolverCallbackUtil.__init__(self, course_vars, courses, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            actual = {} 
            for c_id in self._courses.keys():
                for d in range(self._n_days):

                    # course 3 can only happen on day 2
                    if c_id == 3:
                        if d == 2:
                            duration = self.Value(self._course_vars[c_id, d].duration)
                            if duration == 0:
                                self.msg = "Course 3 has to take place on day 2"
                                self.success = False
                                self.StopSearch()
                        else:
                            duration = self.Value(self._course_vars[c_id, d].duration)
                            if duration != 0:
                                self.msg = "Course 3 cannot take place on day 2"
                                self.success = False
                                self.StopSearch()

                    # course 1 can only happen in the first two periods of days 1 and 2
                    elif c_id == 1:
                        if d == 1:
                            duration = self.Value(self._course_vars[c_id, d].duration)
                            start = self.Value(self._course_vars[c_id, d].start)
                            end = self.Value(self._course_vars[c_id, d].end)
                            if duration == 0 or start != 0 or end != 2:
                                self.msg = "Course 1 has to take place during periods 1 and 2 of day 1"
                                self.success = False
                                self.StopSearch()
                        elif d == 2:
                            duration = self.Value(self._course_vars[c_id, d].duration)
                            start = self.Value(self._course_vars[c_id, d].start)
                            end = self.Value(self._course_vars[c_id, d].end)
                            if duration == 0 or start != 0 or end != 2:
                                self.msg = "Course 1 has to take place during periods 1 and 2 of day 2"
                                self.success = False
                                self.StopSearch()
                        else:
                            duration = self.Value(self._course_vars[c_id, d].duration)
                            if duration != 0:
                                self.msg = "Course 1 cannot take place on days other than 1 and 2"
                                self.success = False
                                self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1


class TestSchedLectureLenCallback(SolverCallbackUtil):

    def __init__(self, course_vars, courses, n_days, n_periods, n_solutions):
        SolverCallbackUtil.__init__(self, course_vars, courses, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            for c_id in self._courses.keys():
                for d in range(self._n_days):
                    duration = self.Value(self._course_vars[c_id, d].duration)
                    if duration and duration not in COURSE_GRANULARITY:
                        self.msg = f"Detected lecture with len {duration}"
                        self.success = False
                        self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1

class TestCourseSched(unittest.TestCase):

    def test_sched_periods_sum(self):
        """ Sum of scheduled periods per course per week
            must be equal to the `n_periods` for the corresponding `Course`.
        """
        c0, c1, c2, c3 = Course(0, 6), Course(1, 6), Course(2, 4), Course(3, 6)
        courses = [c0, c1, c2, c3]
        n_days = 3
        n_periods = 8

        sched = CourseSched(n_days, n_periods)
        sched.create_course_vars(courses)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()

        expected = {}
        for c_id, c in sched.courses.items():
            expected[c_id] = c.n_periods

        n_solutions = 999 
        test_callback = TestSchedPeriodSumCallback(sched.course_vars,
                                                   sched.courses,
                                                   sched.n_days,
                                                   sched.n_periods,
                                                   n_solutions,
                                                   expected)

        solver = sched.solve(test_callback)
        self.assertEqual(test_callback.actual, test_callback.expected)

    def test_unavailability_constraints(self):
        c0, c1, c2, c3 = Course(0, 6), Course(1, 4), Course(2, 6), Course(3, 6)
        courses = [c0, c1, c2, c3]
        n_days = 3
        n_periods = 10

        sched = CourseSched(n_days, n_periods)
        sched.create_course_vars(courses)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        
        # Course 3 can only happen on day 2
        sched.add_unavailability_constraints(3, 0, [(0, 9)])
        sched.add_unavailability_constraints(3, 1, [(0, 9)])

        # Course 1 can only happen in the first two periods of days 1 and 2
        sched.add_unavailability_constraints(1, 0, [(0, 9)])
        sched.add_unavailability_constraints(1, 1, [(2, 9)])
        sched.add_unavailability_constraints(1, 2, [(2, 9)])

        n_solutions = 999 
        test_callback = TestSchedUnavailabilityConstraintsCallback(sched.course_vars,
                                                                   sched.courses,
                                                                   sched.n_days,
                                                                   sched.n_periods,
                                                                   n_solutions)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

    def test_lecture_len_constraint(self):
        c0, c1, c2, c3 = Course(0, 6), Course(1, 4), Course(2, 6), Course(3, 6)
        courses = [c0, c1, c2, c3]
        n_days = 3
        n_periods = 10

        sched = CourseSched(n_days, n_periods)
        sched.create_course_vars(courses)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()

        n_solutions = 999 
        test_callback = TestSchedLectureLenCallback(sched.course_vars,
                                                    sched.courses,
                                                    sched.n_days,
                                                    sched.n_periods,
                                                    n_solutions)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

if __name__ == '__main__':
    unittest.main()


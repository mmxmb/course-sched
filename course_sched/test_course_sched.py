import unittest
from ortools.sat.python import cp_model
from course_sched import CourseSched, Course, Curriculum, ModelVar, SolverCallbackUtil, COURSE_GRANULARITY

N_SOL_PER_TEST = 4999

class TestSchedPeriodSumCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days, n_periods, n_solutions, expected):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.expected = expected
        self.actual = None

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            self.actual = {} 
            for cur_id, cur in self._curricula.items():
                self.actual[cur_id] = {}
                for c_id in cur.courses.keys():
                    self.actual[cur_id][c_id] = 0
                    for d in range(self._n_days):
                        duration = self.Value(self._model_vars[cur_id, d, c_id].duration)
                        self.actual[cur_id][c_id] += duration
            if self.actual != self.expected:
                self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1


class TestSchedUnavailabilityConstraintsCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days, n_periods, n_solutions):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            actual = {} 
            for cur_id, cur in self._curricula.items():
                for c_id in cur.courses.keys():
                    for d in range(self._n_days):

                        # course 3 can only happen on day 2
                        if c_id == 3:
                            if d == 2:
                                duration = self.Value(self._model_vars[cur_id, d, c_id].duration)
                                if duration == 0:
                                    self.msg = "Course 3 has to take place on day 2"
                                    self.success = False
                                    self.StopSearch()
                            else:
                                duration = self.Value(self._model_vars[cur_id, d, c_id].duration)
                                if duration != 0:
                                    self.msg = "Course 3 cannot take place on day 2"
                                    self.success = False
                                    self.StopSearch()

                        # course 1 can only happen in the first two periods of days 1 and 2
                        elif c_id == 1:
                            duration = self.Value(self._model_vars[cur_id, d, c_id].duration)
                            start = self.Value(self._model_vars[cur_id, d, c_id].start)
                            end = self.Value(self._model_vars[cur_id, d, c_id].end)
                            if d == 1:
                                if duration == 0 or start != 0 or end != 2:
                                    self.msg = "Course 1 has to take place during periods 1 and 2 of day 1"
                                    self.success = False
                                    self.StopSearch()
                            elif d == 2:
                                if duration == 0 or start != 0 or end != 2:
                                    self.msg = "Course 1 has to take place during periods 1 and 2 of day 2"
                                    self.success = False
                                    self.StopSearch()
                            else:
                                if duration != 0:
                                    self.msg = "Course 1 cannot take place on days other than 1 and 2"
                                    self.success = False
                                    self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1


class TestSchedLectureLenCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days, n_periods, n_solutions):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            for cur_id, cur in self._curricula.items():
                for d in range(self._n_days):
                    for c_id in cur.courses.keys():
                        duration = self.Value(self._model_vars[cur_id, d, c_id].duration)
                        if duration and duration not in COURSE_GRANULARITY:
                            self.msg = f"Detected lecture with len {duration}"
                            self.success = False
                            self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1

class TestCurriculaSyncCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days, n_periods, n_solutions, course_to_curricula):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.course_to_curricula = course_to_curricula
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            for d in range(self._n_days):
                for c_id, cur_ids in self.course_to_curricula.items():
                    starts, ends = [], []
                    for cur_id in cur_ids:
                        start = self.Value(self._model_vars[cur_id, d, c_id].start)
                        end = self.Value(self._model_vars[cur_id, d, c_id].end)
                        starts.append(start)
                        ends.append(end)
                    if len(set(starts)) > 1 or len(set(ends)) > 1:
                        self.msg = f"Courses shared across curricula are not in sync"
                        self.success = False
                        self.StopSearch()
        else:
            self.StopSearch()
        self._solution_count += 1

class TestLectureSymmetryCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days, n_periods, n_solutions):
        SolverCallbackUtil.__init__(self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            for cur_id, cur in self._curricula.items():
                for c_id, c in cur.courses.items():

                    mon_start = self.Value(self._model_vars[cur_id, 0, c_id].start)
                    tue_start = self.Value(self._model_vars[cur_id, 1, c_id].start)
                    wed_start = self.Value(self._model_vars[cur_id, 2, c_id].start)
                    thu_start = self.Value(self._model_vars[cur_id, 3, c_id].start)
                    fri_start = self.Value(self._model_vars[cur_id, 4, c_id].start)
                    mon_duration = self.Value(self._model_vars[cur_id, 0, c_id].duration)
                    tue_duration = self.Value(self._model_vars[cur_id, 1, c_id].duration)
                    wed_duration = self.Value(self._model_vars[cur_id, 2, c_id].duration)
                    thu_duration = self.Value(self._model_vars[cur_id, 3, c_id].duration)
                    fri_duration = self.Value(self._model_vars[cur_id, 4, c_id].duration)

                    if tue_duration and thu_duration:
                        if tue_start != thu_start or tue_duration != thu_duration:
                            self.msg = f"Courses on Tue and Thu are not symmetric"
                            self.success = False
                            self.StopSearch()
                        elif mon_duration or wed_duration or fri_duration:
                            self.msg = f"When course is on Tue and Thu, there should be no courses on other days" 
                            self.success = False
                            self.StopSearch()
                    elif mon_duration and wed_duration and not fri_duration:
                        if mon_start != wed_start or mon_duration != wed_duration:
                            self.msg = f"Courses on Mon and Wed are not symmetric"
                            self.success = False
                            self.StopSearch()
                        elif tue_duration or thu_duration:
                            self.msg = f"When course is on Mon and Wed, there should be no courses on other days" 
                            self.success = False
                            self.StopSearch()
                    elif mon_duration and wed_duration and fri_duration:
                        if mon_start != wed_start or mon_duration != wed_duration or \
                                wed_start != fri_start or wed_duration != fri_duration or \
                                mon_start != fri_start or mon_duration != fri_duration:
                            self.msg = f"Courses on Mon and Wed and Fri are not symmetric"
                            self.success = False
                            self.StopSearch()
                        elif tue_duration or thu_duration:
                            self.msg = f"When course is on Mon and Wed and Fri, there should be no courses on other days" 
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
        c4, c5, c6, c7 = Course(4, 6), Course(5, 4), Course(6, 4), Course(7, 4)
        courses0 = [c0, c1, c2, c3]
        courses1 = [c4, c5, c6, c7]
        cur0 = Curriculum(0, courses0)
        cur1 = Curriculum(1, courses1)
        curricula = [cur0, cur1]
        n_days = 3
        n_periods = 8

        sched = CourseSched(n_days, n_periods, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()

        expected = {}
        for cur_id, cur in sched.curricula.items():
            expected[cur_id] = {}
            for c_id, c in cur.courses.items():
                expected[cur_id][c_id] = c.n_periods

        test_callback = TestSchedPeriodSumCallback(sched.model_vars,
                                                   sched.curricula,
                                                   sched.n_days,
                                                   sched.n_periods,
                                                   N_SOL_PER_TEST,
                                                   expected)

        solver = sched.solve(test_callback)
        self.assertEqual(test_callback.actual, test_callback.expected)

    def test_unavailability_constraints(self):
        """ Intervals marked as unavailable for particular courses
            must not be taken by those courses.
        """
        c0, c1, c2, c3 = Course(0, 6), Course(1, 4), Course(2, 6), Course(3, 6)
        courses = [c0, c1, c2, c3]
        cur = Curriculum(0, courses)
        curricula = [cur]
        n_days = 3
        n_periods = 10

        sched = CourseSched(n_days, n_periods, curricula)
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

        test_callback = TestSchedUnavailabilityConstraintsCallback(sched.model_vars,
                                                                   sched.curricula,
                                                                   sched.n_days,
                                                                   sched.n_periods,
                                                                   N_SOL_PER_TEST)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

    def test_lecture_len_constraint(self):
        """ Lecture lengths must be 2, 3 or 6.
        """
        c0, c1, c2, c3 = Course(0, 6), Course(1, 6), Course(2, 4), Course(3, 6)
        c4, c5, c6, c7 = Course(4, 6), Course(5, 4), Course(6, 4), Course(7, 4)
        courses0 = [c0, c1, c2, c3]
        courses1 = [c4, c5, c6, c7]
        cur0 = Curriculum(0, courses0)
        cur1 = Curriculum(1, courses1)
        curricula = [cur0, cur1]
        n_days = 3
        n_periods = 10

        sched = CourseSched(n_days, n_periods, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()

        test_callback = TestSchedLectureLenCallback(sched.model_vars,
                                                    sched.curricula,
                                                    sched.n_days,
                                                    sched.n_periods,
                                                    N_SOL_PER_TEST)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

    def test_curricula_sync(self):
        """ Courses shared across different curricula must happen at the same time.
        """
        c0, c1, c2, c3 = Course(0, 6), Course(1, 6), Course(2, 4), Course(3, 6)
        c4, c5, c6, c7 = Course(4, 6), Course(5, 4), Course(6, 4), Course(7, 4)
        c8, c9, c10, c11 = Course(8, 6), Course(9, 4), Course(10, 6), Course(11, 4)
        courses0 = [c0, c1, c2, c3, c11]
        courses1 = [c4, c5, c6, c7, c0, c1, c9]
        courses2 = [c0, c5, c6, c3, c10, c8]
        cur0 = Curriculum(0, courses0)
        cur1 = Curriculum(1, courses1)
        cur2 = Curriculum(2, courses2)
        curricula = [cur0, cur1, cur2]
        n_days = 5
        n_periods = 10

        sched = CourseSched(n_days, n_periods, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        sched.add_sync_across_curricula_constraints()

        test_callback = TestCurriculaSyncCallback(sched.model_vars,
                                                  sched.curricula,
                                                  sched.n_days,
                                                  sched.n_periods,
                                                  N_SOL_PER_TEST,
                                                  sched.course_to_curricula)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

    def test_lecture_symmetry(self):
        """ Lectures have to be scheduled symmetrically. I.e. a 1.5 hour lecture at 1PM Tue
            must also be scheduled for 1PM Thu.
        """
        c0, c1, c2, c3 = Course(0, 6), Course(1, 4), Course(2, 6), Course(3, 6)
        c4, c5, c6, c7 = Course(4, 6), Course(5, 4), Course(6, 4), Course(7, 4)
        courses = [c0, c1, c2, c3, c4, c5, c6, c7]
        cur = Curriculum(0, courses)
        curricula = [cur]
        n_days = 5
        n_periods = 8

        sched = CourseSched(n_days, n_periods, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        sched.add_sync_across_curricula_constraints()
        sched.add_lecture_symmetry_constraints()
        
        test_callback = TestLectureSymmetryCallback(sched.model_vars,
                                                    sched.curricula,
                                                    sched.n_days,
                                                    sched.n_periods,
                                                    N_SOL_PER_TEST)

        solver = sched.solve(test_callback)
        test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
        self.assertTrue(test_callback.success, msg=test_msg)

if __name__ == '__main__':
    unittest.main()


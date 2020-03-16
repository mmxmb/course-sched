import unittest
from course_sched import (
        CourseSched,
        COURSE_GRANULARITY,
        Course,
        Curriculum,
        SolverCallbackUtil, 
        SchedPartialSolutionSerializer
        )
import os
import sys
from schema import SchemaError
sys.path.append(os.path.abspath('./api_schema'))
from api_schema import response_schema

N_SOL_PER_TEST = 100

class TestSoftTotalTimeConstraintCallback(SolverCallbackUtil):

    def __init__(self, model_vars, curricula, n_days,
                 n_periods,soft_min, soft_max, n_solutions):
        SolverCallbackUtil.__init__(
            self, model_vars, curricula, n_days, n_periods, n_solutions)
        self.success = True
        self.msg = ""
        self._solution_count = 0
        self.soft_max = soft_max
        self.soft_min = soft_min

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            for d in range(self._n_days):
                for cur_id, cur in self._curricula.items():

                    intervals_dictionary = {}  # key map of start_of_lecture -> end_of_lecture
                    sum_durations_low = 0

                    for c_id, c in cur.courses.items():

                        #calulate sum_durations_low i.e sum of durations of lectures of all courses of a particular curriculum on a particular day
                        lecture_duration = self.Value(self.model_vars[cur_id, d, c_id].duration)
                        sum_durations_low = sum_durations_low + lecture_duration

                        #calulate sum_durations_high i.e total time (i.e. end of last course - start of first course)

                        start_of_lecture = self.Value(self.model_vars[cur_id, d, c_id].start)
                        end_of_lecture = self.Value(self.model_vars[cur_id, d, c_id].end)
                        #interval_of_lecture = self.model_vars[cur_id, d, c_id].interval
                        if lecture_duration:
                            intervals_dictionary[start_of_lecture] = end_of_lecture

                    if sum_durations_low <= self.soft_min and sum_durations_low > 0:
                        self.msg = "courses of a particular curriculum on a particular day are scheduled less than 4 periods and more than 0 periods"
                        self.success = False
                        self.StopSearch()


                    end_of_last_lecture = max(intervals_dictionary.values())
                    start_of_first_lecture = min(intervals_dictionary.keys())
                    sum_durations_high = end_of_last_lecture - start_of_first_lecture 

                    
                    if sum_durations_high >= self.soft_max:
                        self.msg = "courses of a particular curriculum on a particular day are scheduled 7 periods or more apart"
                        self.success = False
                        self.StopSearch()

        else:
            self.StopSearch()
        self._solution_count += 1        


class TestCourseSched(unittest.TestCase):

    def test(self):
        self.assertTrue(True)

    def test_soft_constraint_total_time(self):
        c0, c1, c2, c3 = Course('0', 6), Course('1', 6), Course('2', 4), Course('3', 6)
        c4, c5, c6, c7 = Course('4', 6), Course('5', 4), Course('6', 4), Course('7', 4)
        courses0 = [c0, c1, c2, c3]
        courses1 = [c4, c5, c6, c7]
        cur0 = Curriculum('0', courses0)
        cur1 = Curriculum('1', courses1)
        curricula = [cur0, cur1]
        n_days = 5
        n_periods = 27

        sched = CourseSched(n_days, n_periods, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        sched.add_sync_across_curricula_constraints()
        sched.add_lecture_symmetry_constraints()



        soft_min, soft_max = 4, 14

        sched.add_soft_total_time_constraints(soft_min,soft_max,1,1)
        test_callback = TestSoftTotalTimeConstraintCallback(sched.model_vars,
                                                   sched.curricula,
                                                   sched.n_days,
                                                   sched.n_periods,
                                                   soft_min,
                                                   soft_max,
                                                   N_SOL_PER_TEST)

        sched.solve(test_callback,obj_proximity_delta=0)
        
        if test_callback._solution_count:
            # self.assertTrue(True)
            test_msg = test_callback.msg + "\n" + test_callback.sol_to_str()
            self.assertTrue(test_callback.success, msg=test_msg)
        else:
            self.fail("Expected to find some solutions")


if __name__ == '__main__':
    unittest.main()

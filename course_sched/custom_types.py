from dataclasses import dataclass
from typing import Tuple, NewType, List
from ortools.sat.python import cp_model

Interval = NewType('Interval', Tuple[int, int])


@dataclass
class ModelVar:
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar
    duration: cp_model.IntVar


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

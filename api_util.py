import os
from dotenv import load_dotenv
load_dotenv()

def course_locks_contains_duplicates(course_locks) -> bool:
    course_lock_ids = {lock['course_id'] for lock in course_locks}
    return len(course_lock_ids) != len(course_locks)

def course_locks_and_constraints_overlap(course_locks, constraints) -> bool:
    course_lock_ids = {lock['course_id'] for lock in course_locks}
    constraints_course_ids = {constraint['course_id'] for constraint in constraints}
    return not course_lock_ids.isdisjoint(constraints_course_ids)

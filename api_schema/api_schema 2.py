import dotenv
import os
from schema import Schema, And, Use, Optional
from dotenv import load_dotenv

load_dotenv()

PERIODS_RANGE = range(int(os.getenv('PERIODS_PER_DAY')))
MAX_SOLS = int(os.getenv('API_MAX_N_SOLUTIONS'))
DAYS_RANGE = range(int(os.getenv('DAYS_PER_WEEK')))
WEEK_N_PERIODS = (4, 6)
DAY_N_PERIODS = (2, 3, 4, 6)

_course_schema = Schema({'course_id': And(str, len), 'n_periods': And(
    Use(int), lambda n: n in WEEK_N_PERIODS)})

_curriculum_schema = Schema({'curriculum_id': And(str, len),
                             'courses': And([_course_schema], len)
                             })

_constraint_schema = Schema({'course_id': And(str, len),
                             'day': And(Use(int), lambda n: n in DAYS_RANGE),
                             'intervals': And([{
                                 'start': And(Use(int), lambda n: n in PERIODS_RANGE),
                                 'end': And(Use(int), lambda n: n in PERIODS_RANGE)
                             }], len)
                             })

_day_sched_schema = Schema({'day': And(Use(int), lambda n: n in DAYS_RANGE),
                            'start': And(Use(int), lambda n: n in PERIODS_RANGE),
                            'duration': And(Use(int), lambda n: n in DAY_N_PERIODS)
                            })

_sched_course_schema = Schema({'course_id': And(str, len),
                               'schedule': And([_day_sched_schema], len)
                               })

_sched_curriculum_schema = Schema({'curriculum_id': And(str, len),
                                   'courses': And([_sched_course_schema], len)
                                   })

request_schema = Schema({'n_solutions': And(Use(int),
                                            lambda n: 1 <= n <= MAX_SOLS),
                         'curricula': And([_curriculum_schema],
                                          len),
                         Optional('constraints'): [_constraint_schema]})

response_schema = Schema({'n_solutions': And(Use(int), lambda n: 0 <= n <= MAX_SOLS),
                          'solutions': [
                              {'solution_id': And(str, len),
                               'curricula': And([_sched_curriculum_schema], len)}
]
})

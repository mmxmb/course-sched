import unittest
import os
from schema import SchemaError

from api_schema import request_schema, response_schema


class TestApiRequestSchema(unittest.TestCase):

    def setUp(self):
        self.payload = {
            'n_solutions': 666,
            'curricula': [
                {
                    'curriculum_id': "hXkY1ChCPUcdRMbz",
                    'courses': [
                        {
                            'course_id': "0UoeRGKWlpKzZgs7",
                            'n_periods': 6,
                        },
                        {
                            'course_id': "FQJSAdpeIy9rJU1H",
                            'n_periods': 6,
                        },
                        {
                            'course_id': "8sMA05cToLsEKB3y",
                            'n_periods': 4,
                        },
                        {
                            'course_id': "BbjRKtortAflVFLL",
                            'n_periods': 6,
                        }
                    ]
                },
                {
                    'curriculum_id': "yGGLYSENM97GC0A3",
                    'courses': [
                        {
                            'course_id': "hFUhTu8WIEeQEQ3i",
                            'n_periods': 4,
                        },
                        {
                            'course_id': "YlFH40I1LBgH9vEI",
                            'n_periods': 6,
                        },
                        {
                            'course_id': "jWtVT6TsTjz0lFQb",
                            'n_periods': 6,
                        },
                        {
                            'course_id': "BbjRKtortAflVFLL",
                            'n_periods': 6,
                        }
                    ]
                }
            ],
            'constraints': [
                {
                    'course_id': "hFUhTu8WIEeQEQ3i",
                    'day': 2,
                    'intervals': [
                        {
                            'start': 0,
                            'end': 4
                        },
                        {
                            'start': 6,
                            'end': 9
                        }
                    ]
                },
                {
                    'course_id': "hFUhTu8WIEeQEQ3i",
                    'day': 4,
                    'intervals': [
                        {
                            'start': 4,
                            'end': 9
                        }
                    ]
                },
                {
                    'course_id': "jWtVT6TsTjz0lFQb",
                    'day': 3,
                    'intervals': [
                        {
                            'start': 10,
                            'end': 14
                        },
                        {
                            'start': 16,
                            'end': 19
                        }
                    ]
                }
            ]
        }

    def test_valid_request_schema(self):
        try:
            request_schema.validate(self.payload)
        except SchemaError as e:
            self.fail(f"Schema validation error: {e}")

    def test_valid_request_schema_no_constraints(self):
        try:
            del self.payload['constraints']
            request_schema.validate(self.payload)
        except SchemaError as e:
            self.fail(f"Schema validation error: {e}")

    def test_invalid_request_schema_missing_field(self):
        del self.payload['n_solutions']
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_too_many_solutions(self):
        os.environ['API_MAX_N_SOLUTIONS'] = '999'
        self.payload['n_solutions'] = 1000
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_empty_curricula(self):
        self.payload['curricula'] = []
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_empty_courses(self):
        for cur in self.payload['curricula']:
            cur['courses'] = []
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_missing_intervals(self):
        for constraint in self.payload['constraints']:
            del constraint['intervals']
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_invalid_interval(self):
        for constraint in self.payload['constraints']:
            constraint['intervals'][0]['duration'] = -1
        self.assertRaises(SchemaError, request_schema.validate, self.payload)

    def test_invalid_request_schema_invalid_day(self):
        for constraint in self.payload['constraints']:
            constraint['intervals'][0]['day'] = -1
        self.assertRaises(SchemaError, request_schema.validate, self.payload)


class TestApiResponseSchema(unittest.TestCase):

    def setUp(self):
        self.payload = {
            'n_solutions': 2,
            'solutions': [
                {
                    'solution_id': 'elpYkxQTNk3KeyYR',
                    'curricula': [
                        {
                            'curriculum_id': "hXkY1ChCPUcdRMbz",
                            'courses': [
                                {
                                    'course_id': "jWtVT6TsTjz0lFQb",
                                    'schedule': [
                                        {
                                            'day': 0,
                                            'start': 2,
                                            'duration': 3
                                        },
                                        {
                                            'day': 2,
                                            'start': 2,
                                            'duration': 3
                                        }
                                    ]
                                },
                                {
                                    'course_id': "hFUhTu8WIEeQEQ3i",
                                    'schedule': [
                                        {
                                            'day': 0,
                                            'start': 4,
                                            'duration': 2
                                        },
                                        {
                                            'day': 2,
                                            'start': 4,
                                            'duration': 2
                                        },
                                        {
                                            'day': 4,
                                            'start': 4,
                                            'duration': 2
                                        }
                                    ]
                                },
                                {
                                    'course_id': "YlFH40I1LBgH9vEI",
                                    'schedule': [
                                        {
                                            'day': 3,
                                            'start': 10,
                                            'duration': 6
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            'curriculum_id': "yGGLYSENM97GC0A3",
                            'courses': [
                                {
                                    'course_id': "jWtGT6TsdfIL2PQb",
                                    'schedule': [
                                        {
                                            'day': 1,
                                            'start': 14,
                                            'duration': 3
                                        },
                                        {
                                            'day': 3,
                                            'start': 14,
                                            'duration': 3
                                        }
                                    ]
                                },
                                {
                                    'course_id': "hFUhTu8WIEeQEQ3i",
                                    'schedule': [
                                        {
                                            'day': 0,
                                            'start': 4,
                                            'duration': 2
                                        },
                                        {
                                            'day': 2,
                                            'start': 4,
                                            'duration': 2
                                        },
                                        {
                                            'day': 4,
                                            'start': 4,
                                            'duration': 2
                                        }
                                    ]
                                },
                                {
                                    'course_id': "Yad8298AsBgH9vEI",
                                    'schedule': [
                                        {
                                            'day': 4,
                                            'start': 20,
                                            'duration': 6
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    'solution_id': 'elpYkxQTNk3KeyYR',
                    'curricula': [
                        {
                            'curriculum_id': "hXkY1ChCPUcdRMbz",
                            'courses': [
                                {
                                    'course_id': "jWtVT6TsTjz0lFQb",
                                    'schedule': [
                                        {
                                            'day': 0,
                                            'start': 11,
                                            'duration': 2
                                        },
                                        {
                                            'day': 2,
                                            'start': 11,
                                            'duration': 2
                                        },
                                        {
                                            'day': 4,
                                            'start': 11,
                                            'duration': 2
                                        }
                                    ]
                                },
                                {
                                    'course_id': "hFUhTu8WIEeQEQ3i",
                                    'schedule': [
                                        {
                                            'day': 3,
                                            'start': 0,
                                            'duration': 6
                                        }
                                    ]
                                },
                                {
                                    'course_id': "YlFH40I1LBgH9vEI",
                                    'schedule': [
                                        {
                                            'day': 2,
                                            'start': 10,
                                            'duration': 6
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            'curriculum_id': "yGGLYSENM97GC0A3",
                            'courses': [
                                {
                                    'course_id': "jWtGT6TsdfIL2PQb",
                                    'schedule': [
                                        {
                                            'day': 0,
                                            'start': 17,
                                            'duration': 3
                                        },
                                        {
                                            'day': 2,
                                            'start': 17,
                                            'duration': 3
                                        }
                                    ]
                                },
                                {
                                    'course_id': "hFUhTu8WIEeQEQ3i",
                                    'schedule': [
                                        {
                                            'day': 3,
                                            'start': 0,
                                            'duration': 6
                                        }
                                    ]
                                },
                                {
                                    'course_id': "Yad8298AsBgH9vEI",
                                    'schedule': [
                                        {
                                            'day': 4,
                                            'start': 20,
                                            'duration': 6
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def test_valid_response_schema(self):
        try:
            response_schema.validate(self.payload)
        except SchemaError as e:
            self.fail(f"Schema validation error: {e}")

    def test_valid_response_schema_no_solutions(self):
        try:
            self.payload['n_solutions'] = 0
            self.payload['solutions'] = []
            response_schema.validate(self.payload)
        except SchemaError as e:
            self.fail(f"Schema validation error: {e}")

    def test_invalid_response_schema_n_solutions(self):
        self.payload['n_solutions'] = -1
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_schema_too_many_solutions(self):
        os.environ['API_MAX_N_SOLUTIONS'] = '999'
        self.payload['n_solutions'] = 1000
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_missing_n_solutions(self):
        del self.payload['n_solutions']
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_missing_courses(self):
        del self.payload['solutions'][0]['curricula'][0]['courses']
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_schema_empty_curricula(self):
        self.payload['solutions'][0]['curricula'] = []
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_missing_start_time(self):
        del self.payload['solutions'][0]['curricula'][0]['courses'][0]['schedule'][0]['start']
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_invalid_start_time(self):
        self.payload['solutions'][0]['curricula'][0]['courses'][0]['schedule'][0]['start'] = 100
        self.assertRaises(SchemaError, response_schema.validate, self.payload)

    def test_invalid_response_invalid_day(self):
        self.payload['solutions'][0]['curricula'][0]['courses'][0]['schedule'][0]['day'] = -1
        self.assertRaises(SchemaError, response_schema.validate, self.payload)


if __name__ == '__main__':
    unittest.main()

import unittest
import os
import json
from schema import SchemaError

from api_schema import request_schema, response_schema


class TestApiRequestSchema(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.getcwd(), 'examples', 'example_sched_request.json')) as f:
            self.payload = json.load(f)
            self.payload['n_solutions'] = 666

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
        with open(os.path.join(os.getcwd(), 'examples', 'example_sched_response.json')) as f:
            self.payload = json.load(f)

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

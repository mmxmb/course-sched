import unittest

import os

from schema import SchemaError

from api_schema.api_schema import response_schema

import json

from api import app
from unittest import TestCase

import sys

class TestIntegrations(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        with open(os.path.join(os.getcwd(), 'examples', 'example_sched_request.json')) as f:
            self.payload = json.load(f)


  # expected_json_response = json.loads(eg_respo_payload)    

    def test_api_response(self):
        response = self.app.post('/sched' , json=self.payload )
        json_response = response.get_json()
        try:
            response_schema.validate(json_response)
        except SchemaError as e:
            self.fail(f"Schema validation error: {e}")

if __name__ == '__main__':
    unittest.main()

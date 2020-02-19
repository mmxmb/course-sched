import unittest

import os

from schema import SchemaError

from api_schema.api_schema import response_schema

import json

from api import app
from unittest import TestCase

import sys

#from requests.exceptions import HTTPError

class TestIntegrations(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        with open(os.path.join(os.getcwd(), 'examples', 'example_sched_request.json')) as f:
            self.payload = json.load(f)


  # expected_json_response = json.loads(eg_respo_payload)    

    def test_api_basicTest(self):
        response = self.app.post('/sched' , json=self.payload )
        json_response = response.get_json()
        #print(json_response)
        #print(self.payload['curricula'][0]['courses'][0]['course_id'])
        #print(self.payload['curricula'][0]['courses'][1]['course_id'])
        #print(self.payload['curricula'][0]['curriculum_id'])
        #print(self.payload['curricula'][1]['curriculum_id'])
        # assert response.status_code == 200
        self.assertEqual(response.status_code, 200 )
            

    def test_api_response_schema(self):
        del self.payload['n_solutions']
        response = self.app.post('/sched' , json=self.payload )
        json_response = response.get_json()
        #print(json_response)
        # assert response.status_code == 200
        self.assertEqual(response.status_code, 400 )
        self.assertEqual(
            json_response, 
            {'message': "Bad request ; request Schema isn't valid"}
        )

    def test_api_courseID_dublicate(self):
        self.payload['curricula'][0]['courses'][0]['course_id'] = 'EECS2021' 
        self.payload['curricula'][0]['courses'][1]['course_id'] = 'EECS2021' 
        response = self.app.post('/sched' , json=self.payload )
        json_response = response.get_json()
        #print(json_response)
        self.assertEqual(response.status_code, 400 )
        self.assertEqual(
            json_response, 
            {'message': 'Bad request ; courses with identical ids in a curriculum'}
        )


    def test_api_curriculumID_dublicate(self):
        self.payload['curricula'][0]['curriculum_id'] = '2nd year Software Engineering' 
        self.payload['curricula'][1]['curriculum_id'] = '2nd year Software Engineering' 
        response = self.app.post('/sched' , json=self.payload )
        json_response = response.get_json()
        #print(json_response)
        self.assertEqual(response.status_code, 400 )
        self.assertEqual(
            json_response, 
            {'message': 'Bad request ; curriculums with identical ids in a curricula'}
        )

    def test_api_if_request_json(self):
        response = self.app.post('/sched' , data='string' )
        json_response = response.get_json()
        #print(json_response)
        #print(self.payload['curricula'][0]['courses'][0]['course_id'])
        #print(self.payload['curricula'][0]['courses'][1]['course_id'])
        #print(self.payload['curricula'][0]['curriculum_id'])
        #print(self.payload['curricula'][1]['curriculum_id'])
        # assert response.status_code == 200
        self.assertEqual(response.status_code, 400 ) 
        self.assertEqual(
            json_response, 
            {'message': "Bad request ; request isn't json"}
        )       


if __name__ == '__main__':
    unittest.main()

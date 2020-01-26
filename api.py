from flask import Flask, request, jsonify
from flask_restful import Resource, Api

from api_schema.api_schema import request_schema
from course_sched.course_sched import CourseSched, Course, Curriculum, SolverCallbackUtil


app = Flask(__name__)
api = Api(app)

example_response = {
    "n_solutions": 2,
    "solutions": [
        {
            "solution_id": "elpYkxQTNk3KeyYR",
            "curricula": [
                {
                    "curriculum_id": "hXkY1ChCPUcdRMbz",
                    "courses": [
                        {
                            "course_id": "jWtVT6TsTjz0lFQb",
                            "schedule": [
                                {
                                    "day": 0,
                                    "start": 2,
                                    "duration": 3
                                },
                                {
                                    "day": 2,
                                    "start": 2,
                                    "duration": 3
                                }
                            ]
                        },
                        {
                            "course_id": "hFUhTu8WIEeQEQ3i",
                            "schedule": [
                                {
                                    "day": 0,
                                    "start": 4,
                                    "duration": 2
                                },
                                {
                                    "day": 2,
                                    "start": 4,
                                    "duration": 2
                                },
                                {
                                    "day": 4,
                                    "start": 4,
                                    "duration": 2
                                }
                            ]
                        },
                        {
                            "course_id": "YlFH40I1LBgH9vEI",
                            "schedule": [
                                {
                                    "day": 3,
                                    "start": 10,
                                    "duration": 6
                                }
                            ]
                        }
                    ]
                },
                {
                    "curriculum_id": "yGGLYSENM97GC0A3",
                    "courses": [
                        {
                            "course_id": "jWtGT6TsdfIL2PQb",
                            "schedule": [
                                {
                                    "day": 1,
                                    "start": 14,
                                    "duration": 3
                                },
                                {
                                    "day": 3,
                                    "start": 14,
                                    "duration": 3
                                }
                            ]
                        },
                        {
                            "course_id": "hFUhTu8WIEeQEQ3i",
                            "schedule": [
                                {
                                    "day": 0,
                                    "start": 4,
                                    "duration": 2
                                },
                                {
                                    "day": 2,
                                    "start": 4,
                                    "duration": 2
                                },
                                {
                                    "day": 4,
                                    "start": 4,
                                    "duration": 2
                                }
                            ]
                        },
                        {
                            "course_id": "Yad8298AsBgH9vEI",
                            "schedule": [
                                {
                                    "day": 4,
                                    "start": 20,
                                    "duration": 6
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "solution_id": "elpYkxQTNk3KeyYR",
            "curricula": [
                {
                    "curriculum_id": "hXkY1ChCPUcdRMbz",
                    "courses": [
                        {
                            "course_id": "jWtVT6TsTjz0lFQb",
                            "schedule": [
                                {
                                    "day": 0,
                                    "start": 11,
                                    "duration": 2
                                },
                                {
                                    "day": 2,
                                    "start": 11,
                                    "duration": 2
                                },
                                {
                                    "day": 4,
                                    "start": 11,
                                    "duration": 2
                                }
                            ]
                        },
                        {
                            "course_id": "hFUhTu8WIEeQEQ3i",
                            "schedule": [
                                {
                                    "day": 3,
                                    "start": 0,
                                    "duration": 6
                                }
                            ]
                        },
                        {
                            "course_id": "YlFH40I1LBgH9vEI",
                            "schedule": [
                                {
                                    "day": 2,
                                    "start": 10,
                                    "duration": 6
                                }
                            ]
                        }
                    ]
                },
                {
                    "curriculum_id": "yGGLYSENM97GC0A3",
                    "courses": [
                        {
                            "course_id": "jWtGT6TsdfIL2PQb",
                            "schedule": [
                                {
                                    "day": 0,
                                    "start": 17,
                                    "duration": 3
                                },
                                {
                                    "day": 2,
                                    "start": 17,
                                    "duration": 3
                                }
                            ]
                        },
                        {
                            "course_id": "hFUhTu8WIEeQEQ3i",
                            "schedule": [
                                {
                                    "day": 3,
                                    "start": 0,
                                    "duration": 6
                                }
                            ]
                        },
                        {
                            "course_id": "Yad8298AsBgH9vEI",
                            "schedule": [
                                {
                                    "day": 4,
                                    "start": 20,
                                    "duration": 6
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

class Scheduler(Resource):
    def post(self):
        print(request.json)
        validated = request_schema.validate(request.json)
        print(validated)
        return jsonify(example_response)

api.add_resource(Scheduler, '/sched')

if __name__ == '__main__':
    app.run(debug=True)

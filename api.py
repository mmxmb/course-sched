
from flask import Flask, request , jsonify
from flask_restful import Resource, Api
import json
import os
from dotenv import load_dotenv
load_dotenv()

from api_schema.api_schema import request_schema
from course_sched.course_sched import CourseSched, Course, Curriculum, SchedPartialSolutionSerializer


app = Flask(__name__)
api = Api(app)

class Version(Resource):
    def get(self):
        resp = {'name': 'course-sched',
                'version': os.environ.get('VERSION', '1.0')}
        return jsonify(resp)


class Scheduler(Resource):
    def post(self):
        periods_per_day = int(os.environ.get("PERIODS_PER_DAY", 26)) 
        n_days = int(os.environ.get("DAYS_PER_WEEK", 5))
        validated = request_schema.validate(request.json)
         
        # for item in request.json:
        n_solutions = validated['n_solutions']
        curricula = validated['curricula']
        constraints = validated['constraints']
        L_curriculums = []

        for curr in curricula: # run through the curriculums
            curriculum_id = curr['curriculum_id']
            courses = curr['courses']
            L_courses = []
        
            for cour in courses: # run through the courses 
                # what happens if courses ids are similar?
                course_id = cour['course_id']
                n_periods = cour['n_periods']
                L_courses.append(Course(course_id ,n_periods))  # calling the Course function in the course_sched class
        
            L_curriculums.append(Curriculum(curriculum_id, L_courses)) # calling the Curriculum function in the course_sched class

        curricula = L_curriculums
        
        sched = CourseSched(n_days, periods_per_day, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        sched.add_sync_across_curricula_constraints()
        sched.add_lecture_symmetry_constraints()


        for const in constraints:
            course_id = const['course_id']
            day = const['day']
            intervals = const['intervals']
            L_intervals = []

            for inter in intervals:
                start = inter['start']
                end   = inter['end']
                L_intervals.append((start, end))
        
            sched.add_unavailability_constraints(course_id, day, L_intervals)




        # instantiate sched with class CourseSched 


        solution_printer = SchedPartialSolutionSerializer(sched.model_vars,
                                                   sched.curricula,
                                                   sched.n_days,
                                                   sched.n_periods,
                                                   n_solutions)
        sched.solve(solution_printer)

        schedule_info = solution_printer.solutions

        return jsonify(schedule_info)

api.add_resource(Scheduler, "/sched")
api.add_resource(Version, "/version")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

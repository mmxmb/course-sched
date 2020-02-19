
from flask import Flask, request , jsonify , make_response ,abort

from flask_restful import Resource, Api
import json
import os
from dotenv import load_dotenv
load_dotenv()

from api_schema.api_schema import request_schema
from course_sched.course_sched import CourseSched, Course, Curriculum, SchedPartialSolutionSerializer


from schema import SchemaError

app = Flask(__name__)
api = Api(app)

@app.errorhandler(400)
def not_found(error):
    print(error) 
    return make_response(jsonify( error=str(error) ), 400)  

@app.errorhandler(404)
def not_found(error):
    print(error)
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

class Version(Resource):
    def get(self):
        resp = {'name': 'course-sched',
                'version': os.environ.get('VERSION', '1.0')}
        return jsonify(resp)


class Scheduler(Resource):
    def post(self):
        periods_per_day = int(os.environ.get("PERIODS_PER_DAY", 26)) 
        n_days = int(os.environ.get("DAYS_PER_WEEK", 5))

        # if request is not json, throw an error
        if not request.json:
            abort(400 , description="Bad request ; request isn't json")

        try:
            validated = request_schema.validate(request.json)
        except SchemaError:
            abort(400 , description="Bad request ; request Schema isn't valid")
         
        # for item in request.json:
        n_solutions = validated['n_solutions']
        curricula = validated['curricula']
        constraints = validated['constraints']
        L_curriculums = []

        Cuids = set()

        for curr in curricula: # run through the curriculums
            curriculum_id = curr['curriculum_id']
            courses = curr['courses']
            L_courses = []

            Coids = set()

            for cour in courses: # run through the courses 
                # what happens if courses ids are similar?
                course_id = cour['course_id']
                n_periods = cour['n_periods']

                # validation: check for similar course ids
                if course_id in Coids:
                    abort(400 , description="Bad request ; courses with identical ids in a curriculum")
                Coids.add(course_id)    

                L_courses.append(Course(course_id ,n_periods))  # calling the Course function in the course_sched class
        
            # validation: check for similar curriculum ids
            if curriculum_id in Cuids:
                abort(400, description="Bad request ; curriculums with identical ids in a curricula")
            Cuids.add(curriculum_id)

            L_curriculums.append(Curriculum(curriculum_id, L_courses)) # calling the Curriculum function in the course_sched class

        curricula = L_curriculums
        
        sched = CourseSched(n_days, periods_per_day, curricula)
        sched.add_no_overlap_constraints()
        sched.add_course_len_constraints()
        sched.add_lecture_len_constraints()
        sched.add_sync_across_curricula_constraints()
        sched.add_lecture_symmetry_constraints()
        
        D_course_day = {}   # dictionary of course ids as keys and days as values.

        for const in constraints:
            course_id = const['course_id']
            day = const['day']
            intervals = const['intervals']
            L_intervals = [] 
            
            for key , value in D_course_day.items():
                if course_id in D_course_day and value == day:
                    abort(400)
                D_course_day.update(course_id = day)

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

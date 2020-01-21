from flask import Flask
from flask_restful import Resource, Api

from api_schema import schema
from course_sched.course_sched import CourseSched, Course, Curriculum, SolverCallbackUtil


app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        data = [{'name': 'Sue', 'age': '28', 'gender': 'Squid'},
                {'name': 'Sam', 'age': '42'},
                {'name': 'Sacha', 'age': '20', 'gender': 'KID'}]
        validated = schema.validate(data)
        return {'hello': 'world'}

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(debug=True)

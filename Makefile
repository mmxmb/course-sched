run-sched:
	python course_sched/course_sched.py

run-api:
	gunicorn --bind :8080 --workers 1 --threads 8 api:app

test:
	python course_sched/test_course_sched.py 
	python api_schema/test_api_schema.py

freeze:
	pip freeze > requirements.txt

autopep8:
	autopep8 --in-place --aggressive --aggressive course_sched/course_sched.py course_sched/test_course_sched.py

lint:
	pylint course_sched

.PHONY: run-sched run-api test freeze autopep8 lint

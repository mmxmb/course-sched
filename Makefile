run:
	python course_sched/course_sched.py

test:
	python course_sched/test_course_sched.py

freeze:
	pip freeze > requirements.txt

autopep8:
	autopep8 --in-place --aggressive --aggressive course_sched/course_sched.py course_sched/test_course_sched.py

lint:
	pylint course_sched

.PHONY: run test freeze

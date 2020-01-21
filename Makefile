run:
	python course_sched/course_sched.py

test:
	python course_sched/course_sched_test.py

freeze:
	pip freeze -r requirements.txt

.PHONY: run test freeze

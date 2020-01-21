run:
	python3 course_sched/course_sched.py

test:
	python3 course_sched/course_sched_test.py

freeze:
	pip3 freeze -r requirements.txt

.PHONY: run test freeze

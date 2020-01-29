#!/bin/bash
app="course-sched"
docker build -t ${app} .
docker run -d -p 41942:8080 \
  --name=${app} \
  -v $PWD:/app ${app}

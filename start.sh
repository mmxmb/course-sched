#!/bin/bash
app="course-sched"
docker build -t ${app} .
docker run -d -p 41942:80 \
  --name=${app} \
  -v $PWD:/app ${app}

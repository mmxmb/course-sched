# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

ENV PERIODS_PER_DAY 27
ENV API_MAX_N_SOLUTIONS 999
ENV DAYS_PER_WEEK 5
ENV PORT 41945
ENV VERSION 1.0

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install -r requirements.txt 

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 api:app

# Course Scheduling Service

## Description

This service uses [Google OR-Tools](https://developers.google.com/optimization) to create valid course schedule for multiple curricula given various constraints.

## How to use

Currently, the API exposes two endpoints:

* POST `/sched` - main endpoint used for scheduling courses. Data has to be supplied in the body in JSON format. Example request body is provided in [examples/example_sched_request.json](https://github.com/mmxmb/course-sched/blob/master/examples/example_sched_request.json).
* GET `/version` - API version. Mainly used to quickly test whether API is reachable or if authentication works.

The service API can be invoked only by authenticated users. Here are some strategies on how to use the API when developing locally and when in production.

### Using course scheduling API locally 

#### Using Docker image

1. Ensure that you have [gcloud](https://cloud.google.com/sdk/gcloud/) installed.
2. Login: `gcloud auth login`
3. Ensure that you have [Docker](https://www.docker.com/) installed and that it is working properly. 
4. Configure Docker with gcloud: `gcloud auth configure-docker`
5. Get `$SHORT_SHA` of the latest commit to [this repo](https://github.com/mmxmb/course-sched/commit/master) (alphanumeric string of length 7 close to the bottom of the linked page).
6. Pull Docker image and run it: `PORT=8080 && docker run -p 9090:${PORT} -e PORT=${PORT} gcr.io/spare-ab/course-sched:$SHORT_SHA`

##### Example

`/version` endpoint:

```
curl localhost:9090/version
```

`/sched` endpoint:

```
curl -X POST -H "Content-type: application/json" --data "@api_schema/example_request.json" localhost:9090/sched
```

#### Using gcloud command line tool

1. Ensure that you have [gcloud](https://cloud.google.com/sdk/gcloud/) installed.
2. Login: `gcloud auth login`.
3. Assuming your user account has `Cloud Run Invoker` role, you can use your identity token to authenticate.

##### Example

`/version` endpoint:

```
curl -i -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://course-sched-6jwajnedta-uc.a.run.app/version
```

`/sched` endpoint:

```
curl -i -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H "Content-type: application/json" --data "@examples/example_sched_request.json" https://course-sched-6jwajnedta-uc.a.run.app/sched
```

##### Using the cloned version of the repo

1. Clone this repo.
2. Follow the steps in [Development](##-development) section on initial setup, envvars and running API locally.
3. Invoke API like in [Docker image case](####-using-docker-image).

### Using course scheduling API in production 

#### Using course scheduler API from App Engine

Course scheduler API can be invoked by service account that App Engine uses. 

##### Example

`/version` endpoint:

```js
const request = require('request-promise');

const receivingServiceURL = 'https://course-sched-6jwajnedta-uc.a.run.app/sched'

// Set up metadata server request
// See https://cloud.google.com/compute/docs/instances/verifying-instance-identity#request_signature
const metadataServerTokenURL = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=';
const tokenRequestOptions = {
  uri: metadataServerTokenURL + receivingServiceURL,
  headers: {
    'Metadata-Flavor': 'Google'
  }
};

// Fetch the token, then provide the token in the request to the receiving service
request(tokenRequestOptions)
  .then((token) => {
    return request(receivingServiceURL).auth(null, null, true, token)
  })
  .then((response) => {
    console.log(response);
  })
  .catch((error) => {
    console.log(error);
});
```

`/sched` endpoint:

```js
var fs = require('fs');
const request = require('request-promise');

const receivingServiceURL = 'https://course-sched-6jwajnedta-uc.a.run.app/sched'

// Set up metadata server request
// See https://cloud.google.com/compute/docs/instances/verifying-instance-identity#request_signature
const metadataServerTokenURL = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=';
const tokenRequestOptions = {
  uri: metadataServerTokenURL + receivingServiceURL,
  headers: {
    'Metadata-Flavor': 'Google'
  }
};

// Fetch the token, then provide the token in the request to the receiving service
request(tokenRequestOptions)
  .then((token) => {
    const options = {
      method: 'POST',
      uri: receivingServiceURL,
      body: JSON.parse(fs.readFileSync('example_request.json', 'utf8')),
      json: true
    };
    return request(options).auth(null, null, true, token)
  })
  .then((response) => {
    console.log(response);
  })
  .catch((error) => {
    console.log(error);
});
```

See more at [Authenticating service-to-service](https://cloud.google.com/run/docs/authenticating/service-to-service).

## Development

# Initial setup

It's best to use a virtual environment when installing dependencies for this project (e.g. `virtualenv`):

1. Install `virtualenv` globally: 

  ```
pip install virtualenv
```

2. Create virtual environment in the root directory of the project:

  ```
virtualenv venv
```
This step creates the directory `venv` containing the virtual environment.

3. Activate virtual enviornment:

  ```
source ./venv/bin/activate
```
Any Python packages installed from now on are installed just for the virtual environment and are available only when the virtual environment is activated.

4. Install dependencies:

  ```
pip install -r requirements.txt
```

---
You can deactivate the virtual environment by entering `deactivate`.

To remove the virtual environment, simply remove the directory `venv` that was created in step 2.

## Environment variables

Create `.env` file in the root with the following contents:

```
ERIODS_PER_DAY=26
API_MAX_N_SOLUTIONS=999
DAYS_PER_WEEK=5
```

## Testing

`unittest` is used for testing. Run tests using:

```
make test
```

## Running the application

### Command line

Run the command-line version of the scheduler using:

```
make run-sched
```

Run API locally with:

```
make run-api
```

## Common problems

### Problem

Sometimes the following error is raised when initializing the scheduler model.

```
ImportError: cannot import name '_message' from 'google.protobuf.pyext' (.../venv/lib/python3.7/site-packages/google/protobuf/pyext/__init__.py)
```

### Solution

Reinstall `protobuf`:

```
pip install --upgrade --force-reinstall protobuf
```

# Course Scheduling Service

## Description

This service uses [Google OR-Tools](https://developers.google.com/optimization) to create valid course schedule for multiple curricula given various constraints.

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
make run
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

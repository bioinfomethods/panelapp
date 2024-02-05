# PanelApp

Panel App is a crowd-sourced repository of information about various gene panels.

## Application overview

Panel App is a project based on Django Framework.
It uses PostgreSQL as database, AWS SQS as message queue backend and AWS S3 for file storage.

Python version: 3.8

Python dependencies are installed via `setup.py`.

> The previous version of the application used a hosted RabbitMQ instance and the local file system for file storage.
> This new version has been refactored to work on AWS, leveraging managed AWS services.
> Using RabbitMQ and the local file system is still possible with the Django settings `./panelapp/panelapp/settings/on-prem.py`,
> but backward compatibility is not fully guaranteed.

All environments are dockerised.

We make a distinction between local development environments and cloud environments, as they use different Dockerfiles and Django settings.

As much as possible, the application follows the [Twelve-Factors App](https://12factor.net/) design principles.

## Cloud environments

All environments, except the local-dev environment, are assumed to run on AWS against actual AWS services.

Dockerfiles for cloud are optimised for security and size.

The application is agnostic to the container scheduler platform it runs in (e.g. Kubernetes, ECS).

Docker-compose and Makefile in [./docker/cloud/](docker/cloud/) are for locally troubleshooting production docker images.
They are NOT supposed to be used to deploy the application in any environment.

## Contributing to PanelApp

All contributions are under [Apache2 license](http://www.apache.org/licenses/LICENSE-2.0.html#contributions).

Check [CONTRIBUTING.md](./CONTRIBUTING.md) on how to contribute.

## Local development

Local-dev uses Docker and the [Docker Compose stack](./docker-compose.yml) included.

Please use the [Makefile](./Makefile) provided to set up the local dev environment.

### Docker-Compose stack

Docker Compose stack includes:

- _Web_ component: a Django app server run with `runserver_plus`.
- _Worker_ component: a Celery application.
- A PostgreSQL instance
- [LocalStack](https://github.com/localstack/localstack), mocking S3 and SQS.

The application source code is mounted from the local machine as volumes into the running containers.
Any change to the code will be immediately reflected.

> If you start the docker-compose cluster directly, without the Makefile, you need to set `TMPDIR` env variable.
> To `/tmp/localstack` on Linux or `/private/tmp/localstack` on OSX.

### Developer machine requirements

Software requirements:

- Docker: tested with Docker 18.09.2 on Mac
- AWS CLI: tested with aws-cli/1.16.156 Python/2.7.16 botocore/1.12.146

Local setup requirements:

- Edit your `/etc/hosts` file adding `localstack` as alias to `localhost`

This is required because [LocalStack](https://github.com/localstack/localstack), mocking AWS services, is running in
the Docker-Compose cluster as `localstack` but exposed to the host machine on localhost on port 4566.

#### Virtualenv Apple M1 Homebrew

These system dependencies are required to set up a virtualenv to use for development:

```shell
$ brew install postgresql@15
$ brew install openssl@3
$ export LDFLAGS="-L/opt/homebrew/opt/openssl@3/lib"
$ export CPPFLAGS="-I/opt/homebrew/opt/openssl@3/include"
```

#### Linux (Ubuntu 22.04)

Depending on your system, some packages might be required:

```shell
$ sudo apt install postgresql-common libpq-dev libcurl4-openssl-dev
```

### Dockerfile

All Python dependencies, including dev and test deps, are installed as editable.

### Native Development lifecycle

1. Launch local support services:
   ```shell
   pushd docker/dev
   docker-compose up -d db localstack
   popd
   ```
2. Create virtual environment:
   ```shell
   python -m venv .venv
   source .venv/bin/activate
   pip install '.[dev,tests]'
   ```
3. Setup environment variables:
   ```shell
   export USE_S3=FALSE
   export DATABASE_USER=panelapp
   export DATABASE_PASSWORD=secret
   export DATABASE_HOST=localhost
   export DATABASE_PORT=5432
   export DATABASE_NAME=panelapp
   export DJANGO_SETTINGS_MODULE=panelapp.settings.dev
   export DJANGO_LOG_LEVEL=DEBUG
   ```
4. Migrate the database:
   ```shell
   python panelapp/manage.py migrate
   ```
5. Create the super-user:
   ```shell
   python panelapp/manage.py createsuperuser
   ```
6. Load database data:
   ```shell
   python panelapp/manage.py loaddata deploy/genes.json.gz
   ```
7. Start web server:
   ```shell
   python panelapp/manage.py runserver
   ```

#### VSCode Setup

Add the following launch configurations:

```
{
    "name": "Django: Run Server",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/panelapp/manage.py",
    "args": ["runserver"],
    "django": true,
    "justMyCode": false
}
{
    "name": "Django: Migrate",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/panelapp/manage.py",
    "args": ["migrate"],
    "django": true,
    "justMyCode": false
}
{
    "name": "Python: Debug Tests",
    "type": "python",
    "request": "launch",
    "program": "${file}",
    "purpose": ["debug-test"],
    "console": "integratedTerminal",
    "env": { "PYTEST_ADDOPTS": "--no-cov" },
    "justMyCode": false
}
```

The first configuration allows you to run and debug local web server instance.

The second configuration allows you to run and debug the database migration process.

The third configuration allows you to use VSCode's [built-in python testing feature](https://code.visualstudio.com/docs/python/testing)
to run and debug tests. See also:

- https://code.visualstudio.com/docs/python/testing#_test-configuration-settings
- https://code.visualstudio.com/docs/python/testing#_debug-tests

### Docker Development lifecycle

You should use the [Makefile](./Makefile) in this directory for all common tasks.

#### Build dev docker images

```bash
$ make build
```

> You must rebuild the base docker images if you change any dependencies in `setup.py`.
> Any other code change does not require to rebuild, as the source code is mounted from the host machine file system
> and installed in editable mode.

#### Run and set up the stack

To start an empty application from scratch (no Panel, but includes Genes data).

1. Start a new dev stack (in detached mode):
   ```bash
   $ make up
   ```
2. Create db schema or apply migration (give few seconds to the db container to start, before running `migrate`):
   ```bash
   $ make migrate
   ```
3. Load gene data:
   ```bash
   $ make loaddata
   ```
   Genes data contains public gene info, such as ensemble IDs, HGNC symbols, OMIM ID.
4. Create all required mock AWS resources, if the do not exist:
   ```bash
   $ make mock-aws
   ```
5. Deploy static files:
   ```bash
   $ make collectstatic
   ```
6. Create admin user
   ```bash
   $ make createsuperuser
   ```
   This is the user to log into the webapp: username=`admin`, pwd=`changeme`, email=`admin@local`

#### Developing and accessing the application

The application is available at `http://localhost:8080/`

The Python code is mounted from the host `<project-root>/panelapp` directory.

**`setup.py`, `setup.cfg`, `MANIFEST.in` and `VERSION` are copied into the container when the Docker image is build.**
Any change to these files (e.g. **changes to dependencies versions**) requires rebuilding the container and restarting
the cluster.

- Run tests:
  ```bash
  $ make tests
  ```
- To tail logs from **all** containers:
  ```bash
  $ make logs
  ```
  To see logs from a single service you must use `docker-compose` or `docker` commands, directly.
- Stop the stack, without losing the state (db content):
  ```bash
  $ make stop
  ```
  Restart after stopping with `start`.
- Tear down the stack destroying the state (db content):
  ```bash
  $ make down
  ```
- The content of mock S3 buckets is actually saved in the temp directory (`/tmp/localstack` on Linux or
  `/private/tmp/localstack` on OSX). When you re-create the cluster and `mock-aws` resources, content of S3 buckets will
  be there. To clear them use:
  ```bash
  $ make clear-s3
  ```
- Run a Django arbitrary command:

  ```bash
  $ make command <command> [<args>...]
  ```

  E.g. to run shell_plus extension to debug models

  ```bash
  $ make command shell_plus
  ```

### Application Configuration

Django settings: [`panelapp.settings.docker-dev`](../../panelapp/panelapp/settings/docker-dev.py).

The [docker-compose.yml](./docker/docker-compose.yml) sets all required environment variables.

By default, it uses mocked S3 and SQS by LocalStack.

> You could run the application against RabbitMQ and the local file system, tweaking
> [docker-dev settings](../../panelapp/panelapp/settings/docker-dev.py) and [docker-compose.yml](./docker/docker-compose.yml),
> but this backward compatibility may be dropped in the future.

Sending email is completely disabled: it only outputs to console.

### LocalStack

The Docker-Compose cluster also includes an instance of [LocalStack](https://github.com/localstack/localstack) running
S3, SQS for local development.

A minimal LocalStack UI is accessible from `http://localhost:8090/`

Service endpoints are LocalStack defaults:

- S3: `http://localhost:4566`
- SQS: `http://localhost:4566`

> If you are running Docker Compose directly (or from the IDE) on OSX, beware that requires the environment variable
> `TMPDIR=/private/tmp/localstack`. Failing to do this causes LocalStack mounting the host directory `/tmp/localstack`
> (default on Linux), but Docker has no write access to `/tmp` on OSX. The symptom will be a number of _Mount denied_
> or permissions errors on starting LocalStack.

#### Differences between AWS LocalStack and real AWS services

- Running containers do not have any IAM Role; AWS credentials are not actually required but all libraries/cli tools
  expect them. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` must be set as environment variables in the running
  container (actual values do not matter).
- [Service endpoints](https://github.com/localstack/localstack#user-content-overview) are different.
  You have to pass `endpoint_url` to most of libraries/CLI commands. Also, you may have to disable `https` with
  `use_ssl=False` as LocalStack uses http while S3, for example, uses https by default.
- Containers running inside the docker-compose cluster see all LocalStack service coming from `localstack` host. From
  the
  host machine they are actually exposed to `localhost`. To allow resources hosted at `localstack` to be accessible on
  the host machine:
  - Linux: Alias `localstack` to `localhost` in the host machine's `/etc/hosts` file.
  - Windows: Add the line `127.0.0.1 localstack` to the host machine's `C:\Windows\System32\drivers\etc\hosts` file.
- LocalStack SES does not support SMTP

#### AWScli-local

It might be handy installing [AWScli-local](https://github.com/localstack/awscli-local) on developer's machine.

It is a wrapper around AWS cli for interacting with LocalStack (it helps with not `--endpoint-url` and providing dummy
credentials on every request).

### Frontend tests

#### Playwright

Frontend testing makes use of the [Playwright](https://playwright.dev/) framework.

##### Updating Playwright

The version of Playwright in the following locations must be kept in sync:

- `package.json`
- `playwright/Dockerfile`
- `.gitlab-ci.yml`

#### Running tests

Seed a local database with test data:

```
python panelapp/manage.py loaddata frontend/tests/data.json
```

For convenience a Makefile command is provided to run the tests on a reproducible platform
that matches the source of truth (CI/CD) using docker.

Before running this command please ensure the image for this is built:

```
docker-compose build playwright
```

Now run the command:

```
make ui-test
```

Tests can be run using [the CLI](https://playwright.dev/docs/running-tests#command-line) directly on a development machine:

```
yarn playwright test
```

They can also be run (among other things) using [the GUI](https://playwright.dev/docs/running-tests#run-tests-in-ui-mode):

```
yarn playwright test --ui
```

#### Creating a test

Tests can be written from scratch or they can be partially generated using [codegen](https://playwright.dev/docs/codegen-intro#running-codegen):

```
yarn playwright codegen localhost:8080
```

This will launch a GUI where interactions will be recorded in a generated test function.

After the interactions are complete the code can be copied into an existing test file.

#### Debugging a test

See [the documentation](https://playwright.dev/docs/running-tests#debugging-tests).

#### Visual changes

Testing includes visual comparison tests that compare a reference snapshot of a page or element
against a screenshot of the same page or element taken at the time of the test.

If a visual change has occurred and it is necessary for this change to be included then the snapshots
that differ must be updated to accommodate this:

```
make update-snapshots
```

The updated snapshots can then be committed alongside the code changes that cause the visual changes.

#### Managing test data

Data for UI testing is stored at `./frontend/tests/data.json` in the Django data dump format.

To make a change to this data:

1. Start up a local instance of PanelApp using the steps earlier in this document.
2. Ensure that there is no data currently in the local database.
3. Load the data into the database: `python panelapp/manage.py loaddata ./frontend/tests/data.json`
4. Use the local PanelApp instance to put it into the desired state, e.g. by adding/removing panels/genes etc.
5. Export the data from the local instance to a JSON file: `python panelapp/manage.py dumpdata | jq 'map(select(.model != "authtoken.token"))' > data.json`
6. Copy the exported `data.json` over the existing one at `./frontend/tests/data.json`
7. Update the visual test snapshots using `make update-snapshots`
8. Commit the changes to the repository

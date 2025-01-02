#################################################################
# This Makefile is for troubleshooting production images locally.
# It is not meant to build, deploy or run any actual environment!
#################################################################

BUILDDIR := .build
DISTDIR := dist
APPDIR :=  panelapp
SOURCEDIR := ../..
DOCKERCOMPOSE := docker compose -f ./docker/docker-compose.yml

# If the first argument is "command"...
ifeq (command,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "command"
  COMMAND_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(COMMAND_ARGS):;@:)
endif

# LocalStack needs a different TMPDIR in OSX
TMPDIR_ORIG := $(TMPDIR)
OS := $(shell uname)
TMPDIR := /tmp/localstack
ifeq ($(OS),Darwin)
  TMPDIR := /private$(TMPDIR)
endif
export TMPDIR := $(TMPDIR)

all: help

e2e-test-functional: up mock-aws collectstatic ## Run e2e functional tests
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npm run build && npx wait-on http://web:8000 && npx playwright test tests/functional/"

e2e-test-bdd: up mock-aws collectstatic ## Run e2e bdd tests
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npx bddgen -c playwright-bdd.config.ts && npx playwright test -c playwright-bdd.config.ts"

e2e-test-visual: up mock-aws collectstatic ## Run e2e visual tests
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npm run build && npx wait-on http://web:8000 && npx playwright test tests/visual/"

update-snapshots: up mock-aws collectstatic ## Update e2e snapshots
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npm run build && npx wait-on http://web:8000 && npx playwright test tests/visual/ --update-snapshots"

test-component: ## Run UI component tests
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npm run test-ct"

update-component-snapshots: ## Update component snapshots
	$(DOCKERCOMPOSE) run --rm playwright /bin/sh -c "npm ci && npx playwright test -c playwright-ct.config.ts --update-snapshots"

clean: ## Remove build directory
	rm -rf $(BUILDDIR)
	rm -rf $(DISTDIR)

build: clean ## Build Docker Images and static files
	$(DOCKERCOMPOSE) build

up: ## Run cluster
	$(DOCKERCOMPOSE) up -d

migrate: ## Create db schema, apply db migration (migrate command)
	$(DOCKERCOMPOSE) exec web manage migrate

loaddata: export AWS_ACCESS_KEY_ID := dummy-key
loaddata: export AWS_SECRET_ACCESS_KEY := dummy-secret
loaddata: ## Load genes files into db (loaddata command)
	aws --endpoint-url=http://localhost:4566 s3 cp ../../deploy/genes.json.gz s3://media-bucket/genes.json.gz
	$(DOCKERCOMPOSE) exec web /bin/sh -c "python -c \"import boto3,botocore;boto3.resource('s3',use_ssl=False, endpoint_url='http://localstack:4566').Bucket('media-bucket').download_file('genes.json.gz', '/var/tmp/genes.json.gz')\"; manage loaddata --verbosity 3 /var/tmp/genes.json; rm /var/tmp/genes.json.gz"
	aws --endpoint-url=http://localhost:4566 s3 rm s3://media-bucket/genes.json.gz


collectstatic: ## Deploy static files (collectstatic command)
	$(DOCKERCOMPOSE) exec web manage collectstatic --noinput

createsuperuser: ## Create superuser (username: 'admin', pwd: 'changeme', email: `admin@local`)
	$(DOCKERCOMPOSE) exec web /bin/sh -c "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@local', 'changeme')\" | manage shell"

command: ## Run a generic command, passed as additional argument(s)
	$(DOCKERCOMPOSE) exec web manage $(COMMAND_ARGS)

stop: ## Stop cluster, without destroying it
	$(DOCKERCOMPOSE) stop

start: ## Restart a stopped cluster
	$(DOCKERCOMPOSE) start

down: ## Destroy cluster
	$(DOCKERCOMPOSE) down

test: tests
tests: ## Run tests
	$(DOCKERCOMPOSE) exec web bash -c 'cd /app ; pytest'

logs: ## Tail all logs
	$(DOCKERCOMPOSE) logs -f

mock-aws: export AWS_DEFAULT_REGION := eu-west-2
mock-aws: export AWS_ACCESS_KEY_ID := dummy-key
mock-aws: export AWS_SECRET_ACCESS_KEY := dummy-secret
mock-aws: .mock-s3-static .mock-s3-media .mock-sqs-queue ## Create all mock AWS resources

clear-s3: ## Clear mock S3 buckets
	rm -rf $(TMPDIR)/*

help:	## display this help
	@echo "************************************************"
	@echo "This makefile is for local troubleshooting only"
	@echo "   THIS IS NOT FOR RUNNING PRODUCTION IMAGES"
	@echo "************************************************"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target> [<arguments>]\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2 } END{print ""}' $(MAKEFILE_LIST)

# Helpers

$(BUILDDIR):
	mkdir -p $(BUILDDIR)/$(APPDIR)

define create-s3-bucket-if-not-exits
	@echo "Create s3://$(1) if not exists"
	@aws configure set default.s3.addressing_style path
	@aws --endpoint-url=http://localhost:4566 s3 mb s3://$(1) 2>/dev/null || true
	@aws --endpoint-url=http://localhost:4566 s3api put-bucket-acl --bucket $(1) --acl public-read
endef

define create-sqs-queue-if-not-exists
	@echo "Create sqs queue '$(1)' if not exists"
	@aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name $(1) --attributes VisibilityTimeout=360 2>/dev/null || true
endef

.mock-s3-static: ## Create mock S3 bucket for static files
	$(call create-s3-bucket-if-not-exits,static-bucket)

.mock-s3-media: ## Create mock S3 bucket for media files
	$(call create-s3-bucket-if-not-exits,media-bucket)

.mock-sqs-queue: ## Create mock SQS queue for Celery
	$(call create-sqs-queue-if-not-exists,panelapp)

.PHONY:	all clean .copy_sources .mock-s3-static .mock-s3-media .mock-sqs-queue up down migrate loaddata collectstatic stop start mock-aws createsuperuser command test tests logs clear-s3

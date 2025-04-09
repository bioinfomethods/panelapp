# shellcheck shell=bash
set -euo pipefail
IFS=$'\n\t'

# This script is not meant to be executed on it's own as you can't export vars
# from a script. Instead source this file as part of your job in GitLab CI
# foo:
#   script:
#     - source path/to/this/file

aws sts assume-role \
    --role-arn "${AWS_ASSUME_ROLE}" \
    --role-session-name runner-session > aws_role

AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' aws_role)
AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' aws_role)
AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' aws_role)

export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}

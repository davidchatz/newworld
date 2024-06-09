#!/bin/bash

status=1
tmp=/tmp/$$
cmd=`basename $0`

PROFILE=testnewworld
STACK_NAME=invasions

_cleanup()
{
    rm -rf $tmp
    exit $status
}

trap _cleanup 0 1 2 3

function _usage()
{
    echo "Usage: $cmd init|build|deploy|test|cleanup"
    exit $status
}

if [[ $# -ne 1 ]]
then
    _usage
fi


COLOR_RUN=$(tput setaf 12)
COLOR_HEAD=$(tput setaf 10)
COLOR_ERR=$(tput setaf 1)
COLOR_NOTE=$(tput setaf 5)
COLOR_WARN=$(tput setaf 3)
COLOR_OFF=$(tput sgr0)

# Run a command, display but ignore errors
function _run()
{
    echo $COLOR_RUN$@$COLOR_OFF
    "$@"
    return $?
}

# Run a command and exit on error
function _walk()
{
    echo $COLOR_RUN$@$COLOR_OFF
    "$@"
    r=$?
    if [[ $r -ne 0 ]]
    then
        _error "Stopping on error ($r)"
        exit 1
    fi
    return $r
}

function _note()
{
    echo
    echo "$COLOR_NOTE$@$COLOR_OFF"
}

function _warn()
{
    echo
    echo "$COLOR_WARN$@$COLOR_OFF"
}

function _header()
{
    echo
    echo
    echo "$COLOR_HEAD=== "$@" ===$COLOR_OFF"
    echo
}

function _error()
{
    echo
    echo "$COLOR_ERR"$@"$COLOR_OFF"
    echo
    exit 1
}


REGION=$(aws configure get region --profile $PROFILE)
if [[ -z "$REGION" ]]
then
    _note "Defaulting to ap-southeast-2"
    REGION=ap-southeast-2
fi

OPTIONS="--region $REGION --profile $PROFILE"

ACCOUNT=$(aws sts get-caller-identity $OPTIONS --query Account --output text)
if [[ -z "$ACCOUNT" ]]
then
    _error "Unable to determine AWS Account ID, credentials may have expired."
fi


function _empty_bucket()
{
    if ! aws s3api head-bucket $OPTIONS --bucket $1 2>&1 | grep -q 404;
    then
        _run aws s3 rm $OPTIONS --recursive s3://$1
    fi
}

function _init()
{
    _header "Generate samconfig.toml"

    cat << EOF > samconfig.toml
version = 0.1

[default]
[default.global]
[default.global.parameters]
stack_name = "$STACK_NAME"
profile = "$AWS_PROFILE"

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND"
confirm_changeset = false
fail_on_empty_changeset = false
resolve_s3 = true

[default.sync.parameters]
watch = true

[default.local_start_api.parameters]
warm_containers = "EAGER"

[prod]
[prod.sync]
[prod.sync.parameters]
watch = false
EOF
}

function _build()
{
    _header "SAM build"
    _walk sam build
}

function _update_env()
{
    _header "Update environment variables"

    BUCKET=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`Bucket`].{id:OutputValue}' \
            --output text)

    TABLE=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`Table`].{id:OutputValue}' \
            --output text)

    STEP=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`StepFunctionArn`].{id:OutputValue}' \
            --output text)

    URL=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`InteractionsEndpointUrl`].{id:OutputValue}' \
            --output text)
    
    cat << EOF > .env
BUCKET_NAME=$BUCKET
TABLE_NAME=$TABLE
PROCESS_STEP_FUNC=$STEP
WEBHOOK_URL=$URL
PROFILE=$PROFILE
POWERTOOLS_LOG_LEVEL=info
EOF
}

function _deploy()
{
    _header "SAM deploy to $REGION in $ACCOUNT"
    _walk sam deploy
    _update_env
}

function _test()
{
    _header "Test deployment"
    _walk pytest
}

function _delete()
{
    _header "SAM delete"
    _walk sam delete
}

case $1 in

    init)
        _init
        ;;

    build)
        _build
        ;;

    deploy)
        _deploy
        ;;

    test)
        _test
        ;;

    cleanup)
        _delete
        ;;

    *)
        _usage
        ;;

esac

status=0
#!/bin/bash

status=1
tmp=/tmp/$$
cmd=`basename $0`
pids=""

AWS_PROFILE=testnewworld
STACK_NAME=invasions
LOG_LEVEL=info

_cleanup()
{
    rm -rf $tmp
    if [[ -n "$pids" ]]
    then
        kill $pids
    fi
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


REGION=$(aws configure get region --profile $AWS_PROFILE)
if [[ -z "$REGION" ]]
then
    _note "Defaulting to ap-southeast-2"
    REGION=ap-southeast-2
fi

OPTIONS="--region $REGION --profile $AWS_PROFILE"

ACCOUNT=$(aws sts get-caller-identity $OPTIONS --query Account --output text)
if [[ -z "$ACCOUNT" ]]
then
    _error "Unable to determine AWS Account ID, credentials may have expired."
fi

TEST_BUCKET=${STACK_NAME}-test-${ACCOUNT}-${REGION}

function _create_bucket()
{
    if aws s3api head-bucket $OPTIONS --bucket $1 2>&1 | grep -q 404;
    then
        _walk aws s3 mb $OPTIONS s3://$1 
        sleep 2
    fi
}

function _empty_bucket()
{
    if ! aws s3api head-bucket $OPTIONS --bucket $1 2>&1 | grep -q 404;
    then
        _run aws s3 rm $OPTIONS --recursive s3://$1
    fi
}

function _delete_bucket()
{
    if ! aws s3api head-bucket $OPTIONS --bucket $1 2>&1 | grep -q 404;
    then
        _run aws s3 rm $OPTIONS --recursive s3://$1
        _run aws s3 rb $OPTIONS s3://$1
    fi  
}

function _sync_samples()
{
    _header "Create and populate S3 bucket with test images"

    _create_bucket $TEST_BUCKET
    _walk aws s3 sync $OPTIONS tests/samples s3://$TEST_BUCKET --exclude .DS_store

    _header "Sync some samples to target bucket"

    BUCKET=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`Bucket`].{id:OutputValue}' \
            --output text)

    _walk aws s3 sync $OPTIONS s3://$TEST_BUCKET/20240611-rw s3://$BUCKET/ladders/20240611-rw/ --exclude .DS_store
    _walk aws s3 sync $OPTIONS s3://$TEST_BUCKET/20240524-bw-board s3://$BUCKET/roster/20240524-bw/ --exclude .DS_store
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
    _walk sam build --use-container
}

function _update_env()
{
    _header "Update environment variable files"

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

    DEAD_HAND_STEP=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`DeadHandStepFunctionArn`].{id:OutputValue}' \
            --output text)

    PROCESS_STEP=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`ProcessStepFunctionArn`].{id:OutputValue}' \
            --output text)

    URL=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`InteractionsEndpointUrl`].{id:OutputValue}' \
            --output text)
    
    cat << EOF > .env
BUCKET_NAME=$BUCKET
TEST_BUCKET_NAME=$TEST_BUCKET
TABLE_NAME=$TABLE
DEAD_HAND_STEP_FUNC=$DEAD_HAND_STEP
PROCESS_STEP_FUNC=$PROCESS_STEP
WEBHOOK_URL=$URL
AWS_PROFILE=$AWS_PROFILE
POWERTOOLS_LOG_LEVEL=$LOG_LEVEL
EOF
    cat .env

    cat << EOF > .env.json
{
    "Download": {
        "POWERTOOLS_SERVICE_NAME": "Download",
        "POWERTOOLS_LOG_LEVEL": "$LOG_LEVEL",
        "BUCKET_NAME": "$BUCKET"
    },
    "Ladder": {
        "POWERTOOLS_SERVICE_NAME": "Ladder",
        "POWERTOOLS_LOG_LEVEL": "$LOG_LEVEL",
        "BUCKET_NAME": "$BUCKET",
        "TABLE_NAME": "$TABLE",
        "DEAD_HAND_STEP_FUNC": "$DEAD_HAND_STEP",
        "PROCESS_STEP_FUNC": "$PROCESS_STEP",
        "WEBHOOK_URL": "$URL"
    }
}
EOF
}

function _deploy()
{
    _header "SAM deploy to $REGION in $ACCOUNT"
    _walk sam deploy
    _update_env
}

function _cleanup_table()
{
    _header "Cleanup table"
    TABLE=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`Table`].{id:OutputValue}' \
            --output text)
    _run ./src/layer/tests/delete_items.py $AWS_PROFILE $TABLE
}

function _cleanup_bucket()
{
    _header "Cleanup bucket"
    BUCKET=$(aws cloudformation describe-stacks \
            $OPTIONS \
            --stack-name $STACK_NAME \
            --query 'Stacks[].Outputs[?OutputKey==`Bucket`].{id:OutputValue}' \
            --output text)
    _empty_bucket $BUCKET
}

function _cleanup_test_bucket()
{
    _header "Cleanup test image bucket"
    _empty_bucket $TEST_BUCKET
    _delete_bucket $TEST_BUCKET
}

function _test()
{
    _cleanup_table
    # _cleanup_bucket
    _sync_samples
    _header "Test deployment"
    _walk pytest
}

function _local_test_prep()
{
    _header "Prepare local test of lambda functions"
    _walk sam build --use-container
}

function _test_local()
{
    if [[ $# -eq 1 ]]
    then
        TESTS=$1
    else
        TESTS=tests
    fi

    _cleanup_table
    # _cleanup_bucket
    _sync_samples
    _header "Test download lambda"
    pid=$(lsof -i tcp:3001 -t)
    if [[ -n "$pid" ]]
    then
        _warn sam lambda server already running, terminating
        _run kill $pid
    fi
    _note sam local start-lambda --env-vars .env.json --warm-containers eager
    sam local start-lambda --env-vars .env.json --warm-containers eager &
    pid=$!
    pids="$pids $pid"
    _run sleep 15
    _walk pytest $TESTS
    _run kill -s INT $pid
}

function _delete()
{
    _cleanup_test_bucket
    # _cleanup_bucket
    # _cleanup_table
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

    install)
        _build
        _deploy
        ;;

    update-env)
        _update_env
        ;;

    test)
        _test
        ;;

    local-test-prep)
        _local_test_prep
        ;;

    test-local)
        _test_local
        ;;

    all)
        _build
        _deploy
        _test
        _test_local
        ;;

    env)
        _update_env
        ;;

    cleanup)
        _delete
        ;;

    *)
        _usage
        ;;

esac

status=0
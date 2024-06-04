import boto3
import botocore

profile = 'testnewworld'
session = None
lambda_client = None

def get_session():

    if not session:
        session = boto3.session.Session(profile)
    return session

def get_lambda_client(local:bool):

    if lambda_client:
        return lambda_client
    
    if not session:
        session = get_session(profile)

    if local:

        # Create Lambda SDK client to connect to appropriate Lambda endpoint
        lambda_client = session.client('lambda',
            endpoint_url="http://127.0.0.1:3001",
            use_ssl=False,
            verify=False,
            config=botocore.client.Config(
                signature_version=botocore.UNSIGNED,
                read_timeout=15,
                retries={'max_attempts': 0},
            )
        )
    else:
        lambda_client = session.client('lambda')

    return lambda_client
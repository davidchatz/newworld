import boto3
from botocore.config import Config
from botocore import UNSIGNED

class LambdaClient:

    session = None
    lambda_client = None

    def __init__(self, local:bool, profile:str = None):
        if profile:
            self.session = boto3.session.Session(profile_name = profile)
        else:
            self.session = boto3.session.Session()

        if local:
            # Create Lambda SDK client to connect to appropriate Lambda endpoint
            self.lambda_client = self.session.client('lambda',
                endpoint_url="http://127.0.0.1:3001",
                use_ssl=False,
                verify=False,
                config=Config(
                    signature_version=UNSIGNED,
                    read_timeout=15,
                    retries={'max_attempts': 0},
                )
            )
        else:
            lambda_client = self.session.client('lambda')

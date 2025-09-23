import boto3

DEFAULT_PROFILE='PROFILE'
DEFAULT_REGION='ap-southeast-2'

my_session = boto3.session.Session(profile_name=DEFAULT_PROFILE, region_name=DEFAULT_REGION)

def migrate(source, target):
    dynamo_client = my_session.client('dynamodb',)
    dynamo_target_client = my_session.client('dynamodb')

    dynamo_paginator = dynamo_client.get_paginator('scan')
    dynamo_response = dynamo_paginator.paginate(
        TableName=source,
        Select='ALL_ATTRIBUTES',
        ReturnConsumedCapacity='NONE',
        ConsistentRead=True
    )
    for page in dynamo_response:
        for item in page['Items']:
            dynamo_target_client.put_item(
                TableName=target,
                Item=item
            )


if __name__ == '__main__':
    migrate('XX-XX-RESTORE', 'TARGET_TABLE')
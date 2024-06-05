from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .member import Member
from .env import table

class MemberList:

    members: list[Member]

    def __init__(self, day: int, month: int):
        zero_month = '{0:02d}'.format(month)
        zero_day = '{0:02d}'.format(day)
        date = f'{year}{zero_month}{zero_day}'

        response = table.query(KeyConditionExpression=Key('invasion').eq('#member'))
        print(response)

        if not response.get('Items', None):
            mesg = f'No members found'
        else:
            items = response["Items"]

            body = f"player,faction,start\n"
            for player in items:
                body += '{id},{faction},{start}\n'.format_map(player)

            filename = f'members/{date}.csv'
            print(f'Writing member list to {bucket_name}/{filename}')
            s3_resource.Object(bucket_name, filename).put(Body=body)

            print(f'Generating presigned URL for {filename}')
            try:
                presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
                mesg = f'# {len(items)} Members\nDownload the report (for 1 hour) from **[here]({presigned})**'
            except ClientError as e:
                print(e)
                mesg = f'Error generating presigned URL for {filename}: {e}'

        return mesg

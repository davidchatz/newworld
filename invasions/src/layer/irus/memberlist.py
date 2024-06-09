from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .member import Member
from .environ import table, logger

class MemberList:

    def __init__(self, day: int, month: int, year:int):
        logger.info(f'MemberList.__init__ {day}/{month}/{year}')

        self.members = []

        zero_month = '{0:02d}'.format(month)
        zero_day = '{0:02d}'.format(day)
        date = f'{year}{zero_month}{zero_day}'

        response = table.query(KeyConditionExpression=Key('invasion').eq('#member'))
        logger.debug(response)

        if not response.get('Items', None):
            logger.info(f'No members found for date {date}')
        else:
            items = response["Items"]
            for i in items:
                self.members.append(Member(i))


    def __str__(self) -> str:
        body = f"player,faction,start\n"
        for m in self.members:
            body += '- {player},{faction},{start}\n'.format_map(m)
        return body


        #     filename = f'members/{date}.csv'
        #     logger.info(f'Writing member list to {bucket_name}/{filename}')
        #     s3_resource.Object(bucket_name, filename).put(Body=body)

        #     print(f'Generating presigned URL for {filename}')
        #     try:
        #         presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
        #         mesg = f'# {len(items)} Members\nDownload the report (for 1 hour) from **[here]({presigned})**'
        #     except ClientError as e:
        #         print(e)
        #         mesg = f'Error generating presigned URL for {filename}: {e}'

        # return mesg

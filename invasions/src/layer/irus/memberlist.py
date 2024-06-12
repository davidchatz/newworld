from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .member import IrusMember
from .environ import IrusResources

resources = IrusResources()
logger = resources.logger
table = resources.table

class IrusMemberList:

    def __init__(self):
        logger.info(f'MemberList.__init__')

        self.members = []

        response = table.query(KeyConditionExpression=Key('invasion').eq('#member'))
        logger.debug(response)

        if not response.get('Items', None):
            logger.info(f'No members found')
        else:
            items = response["Items"]
            for i in items:
                self.members.append(IrusMember(i))


    def __str__(self) -> str:
        body = f"player,faction,start\n"
        for m in self.members:
            body += '{player},{faction},{start}\n'.format_map(m)
        return body

    def markdown(self) -> str:
        body = f"# {len(self.members)} Members\n"
        for m in self.members:
            body += '- {player} ({faction}) started {start}\n'.format_map(m)
        return body

    def count(self) -> int:
        return len(self.members)
    
    def get(self,index:int) -> IrusMember:
        return self.members[index]
    
    def is_member(self, player:str) -> bool:
        for m in self.members:
            if m.player == player:
                return True
        return False

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
